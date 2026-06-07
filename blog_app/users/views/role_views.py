"""
users/views/role_views.py

Role ke liye CRUD API views.

APIView kyun (GenericAPIView ya ModelViewSet kyun nahi)?
    - ModelViewSet: bahut magic, less control
    - GenericAPIView: kuch magic, medium control
    - APIView: zero magic, full control — hum exactly jaante hain kya ho raha hai

Hamari API structure:
    POST   /api/v1/roles/list/     → list (pagination + filter + search + ordering)
    POST   /api/v1/roles/          → create
    GET    /api/v1/roles/<id>/     → detail
    POST   /api/v1/roles/<id>/     → update
    DELETE /api/v1/roles/<id>/     → soft delete
"""

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework import status

from core.pagination import StandardPagination
from core.response import success_response, error_response
from users.models import Role
from users.permissions import RBACPermission
from users.serializers import RoleInputSerializer, RoleOutputSerializer

from drf_spectacular.utils import extend_schema, OpenApiParameter


class RoleListView(APIView):
    """
    POST /api/v1/roles/list/

    List API — POST method kyun?
        Complex filters (arrays, nested objects) GET query params mein
        properly express nahi ho pate. POST body mein structured data
        bhej sakte hain — clean aur scalable.

    Request body (sab optional):
    {
        "search":   "admin",           ← name ya code mein search
        "status":   true,              ← filter by status
        "ordering": "-created_at",     ← column wise sort (- = descending)
        "page":     1,
        "page_size": 10
    }
    """

    permission_classes = [RBACPermission]
    rbac_menu          = "roles_management"
    rbac_action        = "view"

    @extend_schema(
        summary="List Roles",
        description="Paginated list of roles with search, filter, and ordering.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "search":    {"type": "string"},
                    "status":    {"type": "boolean"},
                    "ordering":  {"type": "string", "example": "-created_at"},
                    "page":      {"type": "integer"},
                    "page_size": {"type": "integer"},
                },
            }
        },
        tags=["Roles"],
    )
    def post(self, request):
        body     = request.data
        search   = body.get("search",   "").strip()
        status_f = body.get("status",   None)
        ordering = body.get("ordering", "-created_at")

        # Base queryset — sirf active (non-deleted) records
        qs = Role.objects.select_related(
            "created_by", "updated_by"
        )

        # Global search — name ya code mein
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(code__icontains=search)
            )

        # Status filter
        if status_f is not None:
            qs = qs.filter(status=status_f)

        # Ordering — allowed fields sirf
        allowed_ordering = {"name", "-name", "created_at", "-created_at", "status", "-status"}
        if ordering not in allowed_ordering:
            ordering = "-created_at"
        qs = qs.order_by(ordering)

        # Pagination
        paginator = StandardPagination()
        page      = paginator.paginate_queryset(qs, request)
        serializer = RoleOutputSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class RoleCreateView(APIView):
    """
    POST /api/v1/roles/

    Naya role create karo.
    """

    permission_classes = [RBACPermission]
    rbac_menu          = "roles_management"
    rbac_action        = "add"

    @extend_schema(
        summary="Create Role",
        request=RoleInputSerializer,
        responses={201: RoleOutputSerializer},
        tags=["Roles"],
    )
    def post(self, request):
        serializer = RoleInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation failed.",
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # created_by → logged-in user
        role = serializer.save(created_by=request.user)
        return success_response(
            data=RoleOutputSerializer(role).data,
            message="Role created successfully.",
            status=status.HTTP_201_CREATED,
        )


class RoleDetailView(APIView):
    """
    GET    /api/v1/roles/<id>/   → detail
    POST   /api/v1/roles/<id>/   → update
    DELETE /api/v1/roles/<id>/   → soft delete
    """

    permission_classes = [RBACPermission]
    rbac_menu          = "roles_management"

    def _get_role(self, pk):
        """Helper — role fetch karo ya None return karo."""
        try:
            return Role.objects.select_related(
                "created_by", "updated_by", "deleted_by"
            ).get(pk=pk)
        except Role.DoesNotExist:
            return None

    @extend_schema(
        summary="Role Detail",
        responses={200: RoleOutputSerializer},
        tags=["Roles"],
    )
    def get(self, request, pk):
        self.rbac_action = "view"
        role = self._get_role(pk)
        if not role:
            return error_response("Role not found.", status=status.HTTP_404_NOT_FOUND)
        return success_response(data=RoleOutputSerializer(role).data)

    @extend_schema(
        summary="Update Role",
        request=RoleInputSerializer,
        responses={200: RoleOutputSerializer},
        tags=["Roles"],
    )
    def post(self, request, pk):
        self.rbac_action = "edit"
        role = self._get_role(pk)
        if not role:
            return error_response("Role not found.", status=status.HTTP_404_NOT_FOUND)

        serializer = RoleInputSerializer(role, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(
                message="Validation failed.",
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        role = serializer.save(updated_by=request.user)
        return success_response(
            data=RoleOutputSerializer(role).data,
            message="Role updated successfully.",
        )

    @extend_schema(
        summary="Soft Delete Role",
        responses={200: RoleOutputSerializer},
        tags=["Roles"],
    )
    def delete(self, request, pk):
        self.rbac_action = "delete"
        role = self._get_role(pk)
        if not role:
            return error_response("Role not found.", status=status.HTTP_404_NOT_FOUND)

        role.delete(deleted_by=request.user)
        return success_response(
            data=RoleOutputSerializer(role).data,
            message="Role soft-deleted successfully.",
        )