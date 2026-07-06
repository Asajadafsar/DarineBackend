from rest_framework.permissions import BasePermission


class IsAdminRole(BasePermission):

    def has_permission(self, request, view):

        user = request.user

        if not user or not user.is_authenticated:
            return False

        # SAFE ROLE CHECK (case insensitive + fallback safe)
        role = getattr(user, "role", None)

        if not role:
            return False

        return role.lower() == "admin"
