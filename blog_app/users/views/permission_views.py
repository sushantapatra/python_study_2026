"""
users/views/permission_views.py — RolePermission CRUD API Views

Special feature: Bulk assign
    Ek role + menu ke liye ek saath multiple actions assign karo.

    POST /api/v1/permissions/
    {
        "role": 1,
        "menu": 2,
        "actions": [1, 2, 3]    ← add, edit, view — ek saath
    }
"""

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework import status

from core.pagination import StandardPagination
from core.response import success_response, error_response
from users.models import RolePermission
from users.permissions import RBACPermission
from users.serializers import RolePermissionInputSerializer, RolePermissionOutputSerializer
from drf_spectacular.utils import extend_schema


class RolePermissionListView(APIView):
    """POST /api/v1/permissions/list/"""

    permission_classes = [RBACPermission]
    rbac_menu          = "permissions_management"
    rbac_action        = "view"

    @extend_schema(
        summary="List Role Permissions",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "role":      {"type": "integer"},
                    "menu":      {"type": "integer"},
                    "ordering":  {"type": "string"},
                    "page":      {"type": "integer"},
                    "page_size": {"type": "integer"},
                },
            }
        },
        tags=["Role Permissions"],
    )
    def post(self, request):
        body     = request.data
        role_id  = body.get("role",     None)
        menu_id  = body.get("menu",     None)
        ordering = body.get("ordering", "-created_at")

        qs = RolePermission.objects.select_related(
            "role", "menu", "action", "created_by", "updated_by"
        )

        if role_id:
            qs = qs.filter(role_id=role_id)

        if menu_id:
            qs = qs.filter(menu_id=menu_id)

        allowed_ordering = {"created_at", "-created_at"}
        if ordering not in allowed_ordering:
            ordering = "-created_at"
        qs = qs.order_by(ordering)

        paginator  = StandardPagination()
        page       = paginator.paginate_queryset(qs, request)
        serializer = RolePermissionOutputSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class RolePermissionCreateView(APIView):
    """
    POST /api/v1/permissions/

    Single ya bulk assign:
        Single: {"role": 1, "menu": 2, "action": 3}
        Bulk:   {"role": 1, "menu": 2, "actions": [1, 2, 3]}

    Already exists? → skip (no error), naya create karo.
    """

    permission_classes = [RBACPermission]
    rbac_menu          = "permissions_management"
    rbac_action        = "add"

    @extend_schema(
        summary="Assign Role Permission (single or bulk)",
        request=RolePermissionInputSerializer,
        responses={201: RolePermissionOutputSerializer(many=True)},
        tags=["Role Permissions"],
    )
    def post(self, request):
        serializer = RolePermissionInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation failed.",
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        role    = serializer.validated_data["role"]
        menu    = serializer.validated_data["menu"]
        action  = serializer.validated_data.get("action")
        actions = serializer.validated_data.get("actions", [])

        # Single action → list mein daal do (uniform processing)
        if action and action not in actions:
            actions.append(action)

        created_perms = []
        for act in actions:
            perm, created = RolePermission.objects.get_or_create(
                role=role,
                menu=menu,
                action=act,
                defaults={"created_by": request.user},
            )
            # Agar pehle se soft-deleted tha → restore karo
            if not created and perm.deleted_at:
                perm.restore()
                perm.updated_by = request.user
                perm.save(update_fields=["updated_by"])
            created_perms.append(perm)

        return success_response(
            data=RolePermissionOutputSerializer(created_perms, many=True).data,
            message=f"{len(created_perms)} permission(s) assigned successfully.",
            status=status.HTTP_201_CREATED,
        )


class RolePermissionDetailView(APIView):
    """
    GET    /api/v1/permissions/<id>/  → detail
    DELETE /api/v1/permissions/<id>/  → soft delete (revoke)
    """

    permission_classes = [RBACPermission]
    rbac_menu          = "permissions_management"

    def _get_permission(self, pk):
        try:
            return RolePermission.objects.select_related(
                "role", "menu", "action", "created_by", "updated_by", "deleted_by"
            ).get(pk=pk)
        except RolePermission.DoesNotExist:
            return None

    @extend_schema(
        summary="Permission Detail",
        responses={200: RolePermissionOutputSerializer},
        tags=["Role Permissions"],
    )
    def get(self, request, pk):
        self.rbac_action = "view"
        perm = self._get_permission(pk)
        if not perm:
            return error_response("Permission not found.", status=status.HTTP_404_NOT_FOUND)
        return success_response(data=RolePermissionOutputSerializer(perm).data)

    @extend_schema(
        summary="Revoke Permission (soft delete)",
        responses={200: RolePermissionOutputSerializer},
        tags=["Role Permissions"],
    )
    def delete(self, request, pk):
        self.rbac_action = "delete"
        perm = self._get_permission(pk)
        if not perm:
            return error_response("Permission not found.", status=status.HTTP_404_NOT_FOUND)
        perm.delete(deleted_by=request.user)
        return success_response(
            data=RolePermissionOutputSerializer(perm).data,
            message="Permission revoked successfully.",
        )
