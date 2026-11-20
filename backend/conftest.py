import pytest


def pytest_collection_modifyitems(items):
    """
    Ensure all tests marked with django_db have access to all configured databases
    ('default' and 'market_data') in the two-database architecture.
    """
    for item in items:
        django_db_marker = item.get_closest_marker('django_db')
        if django_db_marker is not None:
            # Upgrade marker to enable access to both database connections
            item.add_marker(pytest.mark.django_db(databases=['default', 'market_data']))
