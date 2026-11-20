import pytest


def pytest_collection_modifyitems(items):
    """
    Ensure all tests marked with django_db have access to all configured databases
    ('default' and 'market_data') in the two-database architecture, while preserving
    any explicit marker options like transaction=True.
    """
    for item in items:
        django_db_marker = item.get_closest_marker('django_db')
        if django_db_marker is not None:
            transaction = django_db_marker.kwargs.get('transaction', False)
            serialized_rollback = django_db_marker.kwargs.get('serialized_rollback', False)
            item.add_marker(
                pytest.mark.django_db(
                    transaction=transaction,
                    databases=['default', 'market_data'],
                    serialized_rollback=serialized_rollback,
                )
            )
