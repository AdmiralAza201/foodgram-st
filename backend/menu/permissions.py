from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthorOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return (
            user
            and user.is_authenticated
            and (
                getattr(obj, 'author_id', None) == user.id
                or user.is_staff
            )
        )
