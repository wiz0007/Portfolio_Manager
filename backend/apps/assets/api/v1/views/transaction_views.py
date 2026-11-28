from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework import serializers as drf_serializers
from rest_framework.response import Response

from apps.assets.api.v1.serializers.details import InvestmentTransactionSerializer
from apps.assets.api.v1.serializers.transaction_entry import RecordTransactionSerializer
from apps.assets.models.investment import Investment
from apps.assets.models.transactions import InvestmentTransaction
from core.permissions import IsAuthenticatedAndEmailVerified


class InvestmentTransactionListCreateView(generics.ListCreateAPIView):
    """List or create immutable transactions for an investment holding with concurrency locking."""
    permission_classes = [IsAuthenticatedAndEmailVerified]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RecordTransactionSerializer
        return InvestmentTransactionSerializer

    def get_investment(self):
        inv_id = self.kwargs.get('investment_id')
        return get_object_or_404(Investment, id=inv_id, user=self.request.user)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx['investment'] = self.get_investment()
        return ctx

    def get_queryset(self):
        inv = self.get_investment()
        return InvestmentTransaction.objects.filter(investment=inv).order_by('-transaction_date', '-created_at')

    @extend_schema(
        summary="Record Investment Transaction",
        description="Records an acquisition (BUY), disposal (SELL), dividend, interest, or fee with row-level locking.",
        request=RecordTransactionSerializer,
        responses={201: InvestmentTransactionSerializer},
        tags=["Investments"],
    )
    def post(self, request, *args, **kwargs):
        inv_id = self.kwargs.get('investment_id')
        with transaction.atomic(using='default'):
            locked_inv = Investment.objects.select_for_update().get(id=inv_id, user=request.user)
            serializer = self.get_serializer(data=request.data, context={'investment': locked_inv})
            serializer.is_valid(raise_exception=True)

            tx_type = serializer.validated_data.get('transaction_type', '').upper()
            if tx_type == 'SELL':
                from apps.analytics.services.investment_performance_service import (
                    InvestmentPerformanceService,
                )
                perf = InvestmentPerformanceService.get_investment_performance(locked_inv)
                units = serializer.validated_data.get('units')
                if units > perf.current_quantity:
                    raise drf_serializers.ValidationError(
                        {"units": f"Cannot sell {units} units: holding only contains {perf.current_quantity} units."}
                    )

            tx = serializer.save(
                investment=locked_inv,
                portfolio=locked_inv.portfolio,
                user=request.user,
                currency=locked_inv.currency,
            )
            return Response(InvestmentTransactionSerializer(tx).data, status=status.HTTP_201_CREATED)


class InvestmentTransactionReverseView(generics.GenericAPIView):
    """Reverses an existing investment transaction atomically by creating a compensating reversal transaction."""
    permission_classes = [IsAuthenticatedAndEmailVerified]
    serializer_class = InvestmentTransactionSerializer

    @extend_schema(
        summary="Reverse Investment Transaction",
        description="Creates an auditable compensating reversal transaction that inverts the economic effect of the target transaction.",
        responses={201: InvestmentTransactionSerializer},
        tags=["Investments"],
    )
    def post(self, request, investment_id, transaction_id):
        with transaction.atomic(using='default'):
            locked_inv = get_object_or_404(
                Investment.objects.select_for_update(),
                id=investment_id,
                user=request.user,
            )
            target_tx = get_object_or_404(
                InvestmentTransaction.objects.select_for_update(),
                id=transaction_id,
                investment=locked_inv,
                user=request.user,
            )

            if target_tx.reversal_of_id:
                return Response(
                    {"detail": "Cannot reverse a transaction that is already a reversal."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if target_tx is already reversed
            if InvestmentTransaction.objects.filter(reversal_of=target_tx).exists():
                return Response(
                    {"detail": "This transaction has already been reversed."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            reason = request.data.get('reason', 'User initiated transaction reversal')
            today = timezone.now().date()

            reversal_tx = InvestmentTransaction(
                investment=locked_inv,
                portfolio=locked_inv.portfolio,
                user=request.user,
                transaction_type='REVERSAL',
                transaction_date=today,
                units=target_tx.units,
                price_per_unit=target_tx.price_per_unit,
                amount=target_tx.amount,
                gross_amount=target_tx.gross_amount,
                fees=target_tx.fees,
                taxes=target_tx.taxes,
                currency=target_tx.currency,
                notes=f"Reversal of transaction {target_tx.id}. Reason: {reason}",
                reversal_of=target_tx,
                reversal_reason=reason,
            )
            reversal_tx.save()

            return Response(InvestmentTransactionSerializer(reversal_tx).data, status=status.HTTP_201_CREATED)
