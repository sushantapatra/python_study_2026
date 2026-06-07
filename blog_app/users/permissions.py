"""
users/permissions.py

Custom DRF Permission Classes — RBAC enforcement.

DRF mein har View pe `permission_classes` set hoti hai.
Hum apni custom class banate hain jo:
    1. User authenticated hai? (JWT valid)
    2. User ka role active hai?
    3. Is menu pe is action ki permission hai?

Usage in views:
    from users.permissions import RBACPermission

    class RoleListCreateView(APIView):
        permission_classes = [RBACPermission]
        rbac_menu   = "roles_management"
        rbac_action = "view"          # GET requests ke liye

HTTP method → action mapping:
    GET    → "view"
    POST   → "view"
    POST   → "add"     (create ke liye)
    PUT    → "edit"
    PATCH  → "edit"
    DELETE → "delete"

Special case:
    POST ka use List API mein bhi hota hai (humara List API POST method se hai)
    Isliye view-level pe rbac_action explicitly set karte hain.
"""

from rest_framework.permissions import BasePermission
from users.models import RolePermission


# HTTP method se default action mapping
METHOD_ACTION_MAP = {
    "GET":    "view",
    "POST":    "view",
    "POST":   "add",
    "PUT":    "edit",
    "PATCH":  "edit",
    "POST":  "edit",
    "DELETE": "delete",
}


class RBACPermission(BasePermission):
    """
    Role-Based Access Control permission check.

    View pe yeh attributes set karne hain:
        rbac_menu   = "roles_management"   ← Menu.code
        rbac_action = "view"               ← Action.code (optional, auto-detect from method)
    """

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        # Step 1: User authenticated hai?
        if not request.user or not request.user.is_authenticated:
            self.message = "Authentication credentials were not provided."
            return False

        # Step 2: User active hai aur soft-deleted nahi?
        if not request.user.is_active or request.user.is_deleted:
            self.message = "Your account is inactive."
            return False

        # Step 3: Superuser → sab allowed
        if request.user.is_superuser:
            return True

        # Step 4: Role assigned hai?
        role = getattr(request.user, "role", None)
        if not role or role.is_deleted or not role.status:
            self.message = "Your role is inactive or not assigned."
            return False

        # Step 5: View pe rbac_menu defined hai?
        rbac_menu = getattr(view, "rbac_menu", None)
        if not rbac_menu:
            # rbac_menu set nahi hai — allow karo (open endpoint)
            return True

        # Step 6: Action determine karo
        rbac_action = getattr(view, "rbac_action", None)
        if not rbac_action:
            rbac_action = METHOD_ACTION_MAP.get(request.method, "view")

        # Step 7: DB se permission check karo
        has_perm = RolePermission.objects.filter(
            role=role,
            menu__code=rbac_menu,
            action__code=rbac_action,
        ).exists()

        if not has_perm:
            self.message = (
                f"You do not have '{rbac_action}' permission "
                f"on '{rbac_menu}'."
            )

        return has_perm


class IsSuperAdmin(BasePermission):
    """
    Sirf Super Admin ke liye — system-level operations.
    Example: User role change karna, system settings.
    """

    message = "Only Super Admins can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_superuser
        )


class IsAuthenticatedActive(BasePermission):
    """
    Authenticated + active user — public-ish endpoints ke liye.
    Example: apna profile dekhna, apna password change karna.
    """

    message = "Authentication required."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and not request.user.is_deleted
        )