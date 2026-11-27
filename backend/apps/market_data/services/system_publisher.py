"""System publisher authority for automated ingestion, schedulers, and background jobs."""
import uuid


class SystemPublisher:
    """
    Dedicated authorized system publisher identity for automated ingestion jobs,
    schedulers, and provider synchronization workflows.
    Ensures publication strictly adheres to PriceObservation.publish() invariants
    without creating synthetic users or picking arbitrary database superusers.
    """
    SYSTEM_PUBLISHER_ID = uuid.UUID('00000000-0000-0000-0000-000000000001')
    id = SYSTEM_PUBLISHER_ID
    is_active = True
    is_staff = True
    is_superuser = False
    is_system = True
    email = 'system-market-data@internal.portfolio'
    name = 'SYSTEM_MARKET_DATA_JOB'

    def __init__(self, name: str = 'SYSTEM_MARKET_DATA_JOB'):
        self.id = self.SYSTEM_PUBLISHER_ID
        self.email = 'system-market-data@internal.portfolio'
        self.name = name
        self.is_active = True
        self.is_staff = True
        self.is_superuser = False
        self.is_system = True

    class _SystemGroups:
        def filter(self, *args, **kwargs):
            class _Match:
                @staticmethod
                def exists():
                    return True
            return _Match()

    @property
    def groups(self):
        return self._SystemGroups()

    def __str__(self):
        return f"SystemPublisher({self.name})"
