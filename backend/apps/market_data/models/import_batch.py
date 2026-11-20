import uuid

from django.db import models

from apps.market_data.models.common import CrossDbQuerySet


class ImportBatchStatus(models.TextChoices):
    PREVIEWED = 'PREVIEWED', 'Previewed'
    COMMITTED = 'COMMITTED', 'Committed as Drafts'
    FAILED = 'FAILED', 'Validation Failed'


class PriceImportBatch(models.Model):
    """
    Audit record for bulk CSV price observation uploads.
    """

    objects = CrossDbQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(
        db_index=True,
        default=uuid.uuid4,
        help_text="Uploader User UUID (Primary DB)",
    )
    filename = models.CharField(max_length=255)
    schema_version = models.CharField(max_length=32, default='1.0')
    total_rows = models.PositiveIntegerField(default=0)
    valid_rows = models.PositiveIntegerField(default=0)
    error_rows = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=32,
        choices=ImportBatchStatus.choices,
        default=ImportBatchStatus.PREVIEWED,
        db_index=True,
    )
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'price_import_batches'
        ordering = ['-created_at']

    def __init__(self, *args, **kwargs):
        u = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if u is not None:
            self.user_id = getattr(u, 'id', u)
            self._cached_user = u if hasattr(u, 'id') else None

    @property
    def user(self):
        if hasattr(self, '_cached_user') and self._cached_user is not None:
            return self._cached_user
        if not self.user_id:
            return None
        from apps.users.models import User
        self._cached_user = User.objects.using('default').filter(id=self.user_id).first()
        return self._cached_user

    @user.setter
    def user(self, value):
        self.user_id = getattr(value, 'id', value) if value else None
        self._cached_user = value

    def __str__(self) -> str:
        return f"ImportBatch({self.filename} - {self.status} [{self.valid_rows}/{self.total_rows}])"


class PriceImportRowError(models.Model):
    """
    Individual row rejection detail in an imported CSV batch.
    Available for operator download and error resolution.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(
        PriceImportBatch,
        on_delete=models.CASCADE,
        related_name='row_errors',
        db_index=True,
    )
    row_number = models.PositiveIntegerField()
    raw_data = models.JSONField(default=dict)
    error_field = models.CharField(max_length=64, blank=True, default='')
    error_message = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'price_import_row_errors'
        ordering = ['batch', 'row_number']

    def __str__(self) -> str:
        return f"RowError(Batch {self.batch_id} Row {self.row_number}: {self.error_field})"
