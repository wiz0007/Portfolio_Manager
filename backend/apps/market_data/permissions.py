from rest_framework import permissions


class IsMarketDataOperator(permissions.BasePermission):
    """
    Grants permission to operators who can collect, draft observations, upload CSVs,
    and generate daily collection worklists.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.groups.filter(name='MarketDataOperator').exists()
        )


class IsMarketDataPublisher(permissions.BasePermission):
    """
    Grants permission to publishers who can approve canonical instruments,
    publish price observations, issue corrections, or reject draft quotes.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.groups.filter(name='MarketDataPublisher').exists()
        )


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Allows read-only access to authenticated users, but requires staff permission for mutation.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or request.user.is_superuser


class IsRequestOwnerOrStaff(permissions.BasePermission):
    """
    Allows creators of an InstrumentRequest to view their own request.
    Only staff can view all or execute state mutations (match, approve, reject).
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff or request.user.is_superuser:
            return True
        return obj.user_id == request.user.id
