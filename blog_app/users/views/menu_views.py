"""
users/views/menu_views.py — Menu CRUD API Views
"""

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework import status

from core.pagination import StandardPagination
from core.response import success_response, error_response
from users.models import Menu
from users.permissions import RBACPermission
from users.serializers import MenuInputSerializer, MenuOutputSerializer
from drf_spectacular.utils import extend_schema


class MenuListView(APIView):
    """POST /api/v1/menus/list/"""

    permission_classes = [RBACPermission]
    rbac_menu          = "menus_management"
    rbac_action        = "view"

    @extend_schema(
        summary="List Menus",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "search":    {"type": "string"},
                    "status":    {"type": "boolean"},
                    "parent":    {"type": "integer", "description": "Filter by parent menu id"},
                    "ordering":  {"type": "string", "example": "order"},
                    "page":      {"type": "integer"},
                    "page_size": {"type": "integer"},
                },
            }
        },
        tags=["Menus"],
    )
    def post(self, request):
        body     = request.data
        search   = body.get("search",   "").strip()
        status_f = body.get("status",   None)
        parent   = body.get("parent",   None)
        ordering = body.get("ordering", "order")

        qs = Menu.objects.select_related(
            "parent", "created_by", "updated_by"
        )

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

        if status_f is not None:
            qs = qs.filter(status=status_f)

        if parent is not None:
            qs = qs.filter(parent_id=parent)

        allowed_ordering = {"name", "-name", "order", "-order", "created_at", "-created_at"}
        if ordering not in allowed_ordering:
            ordering = "order"
        qs = qs.order_by(ordering)

        paginator  = StandardPagination()
        page       = paginator.paginate_queryset(qs, request)
        serializer = MenuOutputSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class MenuCreateView(APIView):
    """POST /api/v1/menus/"""

    permission_classes = [RBACPermission]
    rbac_menu          = "menus_management"
    rbac_action        = "add"

    @extend_schema(
        summary="Create Menu",
        request=MenuInputSerializer,
        responses={201: MenuOutputSerializer},
        tags=["Menus"],
    )
    def post(self, request):
        serializer = MenuInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation failed.",
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        menu = serializer.save(created_by=request.user)
        return success_response(
            data=MenuOutputSerializer(menu).data,
            message="Menu created successfully.",
            status=status.HTTP_201_CREATED,
        )


class MenuDetailView(APIView):
    """
    GET    /api/v1/menus/<id>/  → detail
    POST   /api/v1/menus/<id>/  → update
    DELETE /api/v1/menus/<id>/  → soft delete
    """

    permission_classes = [RBACPermission]
    rbac_menu          = "menus_management"

    def _get_menu(self, pk):
        try:
            return Menu.objects.select_related(
                "parent", "created_by", "updated_by", "deleted_by"
            ).get(pk=pk)
        except Menu.DoesNotExist:
            return None

    @extend_schema(summary="Menu Detail", responses={200: MenuOutputSerializer}, tags=["Menus"])
    def get(self, request, pk):
        self.rbac_action = "view"
        menu = self._get_menu(pk)
        if not menu:
            return error_response("Menu not found.", status=status.HTTP_404_NOT_FOUND)
        return success_response(data=MenuOutputSerializer(menu).data)

    @extend_schema(
        summary="Update Menu",
        request=MenuInputSerializer,
        responses={200: MenuOutputSerializer},
        tags=["Menus"],
    )
    def post(self, request, pk):
        self.rbac_action = "edit"
        menu = self._get_menu(pk)
        if not menu:
            return error_response("Menu not found.", status=status.HTTP_404_NOT_FOUND)

        serializer = MenuInputSerializer(menu, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(
                message="Validation failed.",
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        menu = serializer.save(updated_by=request.user)
        return success_response(
            data=MenuOutputSerializer(menu).data,
            message="Menu updated successfully.",
        )

    @extend_schema(summary="Soft Delete Menu", responses={200: MenuOutputSerializer}, tags=["Menus"])
    def delete(self, request, pk):
        self.rbac_action = "delete"
        menu = self._get_menu(pk)
        if not menu:
            return error_response("Menu not found.", status=status.HTTP_404_NOT_FOUND)
        menu.delete(deleted_by=request.user)
        return success_response(
            data=MenuOutputSerializer(menu).data,
            message="Menu soft-deleted successfully.",
        )