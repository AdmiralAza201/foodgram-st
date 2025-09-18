from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or (
            request.user.is_authenticated and obj.author == request.user
        )
