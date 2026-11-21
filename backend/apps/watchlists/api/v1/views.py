from django.core.exceptions import ObjectDoesNotExist, ValidationError
from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from core.permissions import IsAuthenticatedAndEmailVerified

from apps.watchlists.api.v1.serializers import (
    WatchlistAddSerializer,
    WatchlistItemResponseSerializer,
)
from apps.watchlists.services.watchlist_service import WatchlistService


class WatchlistViewSet(viewsets.ViewSet):
    """
    API endpoint for managing user personal watchlists.
    Guarantees user isolation, uniqueness constraints, and dynamic market data resolution.
    """

    permission_classes = [IsAuthenticatedAndEmailVerified]

    def list(self, request):
        items = WatchlistService.list_items(request.user)
        serializer = WatchlistItemResponseSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        serializer = WatchlistAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        try:
            item = WatchlistService.add_item(
                user=request.user,
                instrument_id=data['instrument_id'],
                notes=data.get('notes', ''),
                target_price=data.get('target_price'),
            )
            annotated = WatchlistService.get_annotated_item_data(item)
            out_serializer = WatchlistItemResponseSerializer(annotated)
            return Response(out_serializer.data, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            msg = e.message if hasattr(e, 'message') else str(e.messages if hasattr(e, 'messages') else e)
            return Response({'detail': msg}, status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist as e:
            return Response({'detail': str(e)}, status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk=None):
        try:
            item = WatchlistService.get_item(request.user, pk)
            serializer = WatchlistItemResponseSerializer(item)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except (ObjectDoesNotExist, ValueError):
            return Response({'detail': 'Watchlist item not found.'}, status=status.HTTP_404_NOT_FOUND)

    def destroy(self, request, pk=None):
        try:
            WatchlistService.remove_item(request.user, pk)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (ObjectDoesNotExist, ValueError):
            return Response({'detail': 'Watchlist item not found.'}, status=status.HTTP_404_NOT_FOUND)
