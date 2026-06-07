"""
users/serializers/permission_serializer.py
"""

from rest_framework import serializers
from users.models import RolePermission, Role, Menu, Action


class RolePermissionOutputSerializer(serializers.ModelSerializer):
    role_name   = serializers.CharField(source="role.name",   read_only=True)
    menu_name   = serializers.CharField(source="menu.name",   read_only=True)
    action_name = serializers.CharField(source="action.name", read_only=True)
    created_by  = serializers.SerializerMethodField()
    updated_by  = serializers.SerializerMethodField()

    class Meta:
        model  = RolePermission
        fields = [
            "id",
            "role",
            "role_name",
            "menu",
            "menu_name",
            "action",
            "action_name",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]

    def get_created_by(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None

    def get_updated_by(self, obj):
        if obj.updated_by:
            return obj.updated_by.get_full_name() or obj.updated_by.email
        return None


class RolePermissionInputSerializer(serializers.ModelSerializer):
    """
    Bulk assign support:
        Single:  {"role": 1, "menu": 2, "action": 3}
        Bulk:    {"role": 1, "menu": 2, "actions": [1, 2, 3]}

    Bulk assign ke liye actions (list) field use karo.
    """

    # Bulk assign ke liye optional list field
    actions = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Action.objects.all()),
        required=False,
        write_only=True,
        help_text="Ek saath multiple actions assign karne ke liye.",
    )

    class Meta:
        model  = RolePermission
        fields = ["role", "menu", "action", "actions"]
        extra_kwargs = {
            "action": {"required": False},
        }

    def validate(self, attrs):
        role    = attrs.get("role")
        menu    = attrs.get("menu")
        action  = attrs.get("action")
        actions = attrs.get("actions")

        if not action and not actions:
            raise serializers.ValidationError(
                {"action": "Either 'action' or 'actions' field is required."}
            )

        # Validate karo ki role aur menu active hain
        if role and (role.is_deleted or not role.status):
            raise serializers.ValidationError({"role": "Selected role is inactive or deleted."})

        if menu and (menu.is_deleted or not menu.status):
            raise serializers.ValidationError({"menu": "Selected menu is inactive or deleted."})

        return attrs