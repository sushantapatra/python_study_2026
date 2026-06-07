"""
users/views/action_views.py — Action CRUD API Views
"""

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework import status

from core.pagination import StandardPagination
from core.response import success_response, error_response
from users.models import Action
from users.permissions import RBACPermission
from users.serializers import ActionInputSerializer, ActionOutputSerializer
from drf_spectacular.utils import extend_schema


class ActionListView(APIView):
    """POST /api/v1/actions/list/"""

    permission_classes = [RBACPermission]
    rbac_menu          = "actions_management"
    rbac_action        = "view"

    @extend_schema(
        summary="List Actions",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "search":    {"type": "string"},
                    "status":    {"type": "boolean"},
                    "ordering":  {"type": "string"},
                    "page":      {"type": "integer"},
                    "page_size": {"type": "integer"},
                },
            }
        },
        tags=["Actions"],
    )
    def post(self, request):
        body     = request.data
        search   = body.get("search",   "").strip()
        status_f = body.get("status",   None)
        ordering = body.get("ordering", "name")

        qs = Action.objects.select_related("created_by", "updated_by")

        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

        if status_f is not None:
            qs = qs.filter(status=status_f)

        allowed_ordering = {"name", "-name", "created_at", "-created_at"}
        if ordering not in allowed_ordering:
            ordering = "name"
        qs = qs.order_by(ordering)

        paginator  = StandardPagination()
        page       = paginator.paginate_queryset(qs, request)
        serializer = ActionOutputSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ActionCreateView(APIView):
    """POST /api/v1/actions/"""

    permission_classes = [RBACPermission]
    rbac_menu          = "actions_management"
    rbac_action        = "add"

    @extend_schema(
        summary="Create Action",
        request=ActionInputSerializer,
        responses={201: ActionOutputSerializer},
        tags=["Actions"],
    )
    def post(self, request):
        serializer = ActionInputSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation failed.",
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        action = serializer.save(created_by=request.user)
        return success_response(
            data=ActionOutputSerializer(action).data,
            message="Action created successfully.",
            status=status.HTTP_201_CREATED,
        )


class ActionDetailView(APIView):
    """
    GET    /api/v1/actions/<id>/  → detail
    POST   /api/v1/actions/<id>/  → update
    DELETE /api/v1/actions/<id>/  → soft delete
    """

    permission_classes = [RBACPermission]
    rbac_menu          = "actions_management"

    def _get_action(self, pk):
        try:
            return Action.objects.select_related(
                "created_by", "updated_by", "deleted_by"
            ).get(pk=pk)
        except Action.DoesNotExist:
            return None

    @extend_schema(summary="Action Detail", responses={200: ActionOutputSerializer}, tags=["Actions"])
    def get(self, request, pk):
        self.rbac_action = "view"
        action = self._get_action(pk)
        if not action:
            return error_response("Action not found.", status=status.HTTP_404_NOT_FOUND)
        return success_response(data=ActionOutputSerializer(action).data)

    @extend_schema(
        summary="Update Action",
        request=ActionInputSerializer,
        responses={200: ActionOutputSerializer},
        tags=["Actions"],
    )
    def post(self, request, pk):
        self.rbac_action = "edit"
        action = self._get_action(pk)
        if not action:
            return error_response("Action not found.", status=status.HTTP_404_NOT_FOUND)

        serializer = ActionInputSerializer(action, data=request.data, partial=True)
        if not serializer.is_valid():
            return error_response(
                message="Validation failed.",
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        action = serializer.save(updated_by=request.user)
        return success_response(
            data=ActionOutputSerializer(action).data,
            message="Action updated successfully.",
        )

    @extend_schema(summary="Soft Delete Action", responses={200: ActionOutputSerializer}, tags=["Actions"])
    def delete(self, request, pk):
        self.rbac_action = "delete"
        action = self._get_action(pk)
        if not action:
            return error_response("Action not found.", status=status.HTTP_404_NOT_FOUND)
        action.delete(deleted_by=request.user)
        return success_response(
            data=ActionOutputSerializer(action).data,
            message="Action soft-deleted successfully.",
        )