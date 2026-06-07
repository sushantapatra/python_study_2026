"""
users/serializers/menu_serializer.py
"""

from rest_framework import serializers
from users.models import Menu


class MenuOutputSerializer(serializers.ModelSerializer):
    created_by  = serializers.SerializerMethodField()
    updated_by  = serializers.SerializerMethodField()
    deleted_by  = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()

    class Meta:
        model  = Menu
        fields = [
            "id",
            "name",
            "code",
            "icon",
            "order",
            "parent",
            "parent_name",
            "status",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
            "deleted_at",
            "deleted_by",
        ]

    def get_created_by(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.email
        return None

    def get_updated_by(self, obj):
        if obj.updated_by:
            return obj.updated_by.get_full_name() or obj.updated_by.email
        return None

    def get_deleted_by(self, obj):
        if obj.deleted_by:
            return obj.deleted_by.get_full_name() or obj.deleted_by.email
        return None

    def get_parent_name(self, obj):
        return obj.parent.name if obj.parent else None


class MenuInputSerializer(serializers.ModelSerializer):

    class Meta:
        model  = Menu
        fields = ["name", "code", "icon", "order", "parent", "status"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Menu name cannot be blank.")
        if len(value) < 2:
            raise serializers.ValidationError("Menu name must be at least 2 characters.")
        return value

    def validate_code(self, value):
        value = value.strip().lower().replace(" ", "_").replace("-", "_")
        if not value:
            raise serializers.ValidationError("Menu code cannot be blank.")
        if not re.match(r'^[a-z0-9_]+$', value):
            raise serializers.ValidationError(
                "Menu code can only contain lowercase letters, numbers, and underscores."
            )
        return value

    def validate_parent(self, value):
        """Parent apna khud ka parent nahi ban sakta."""
        if value and self.instance and value.pk == self.instance.pk:
            raise serializers.ValidationError("A menu cannot be its own parent.")
        return value

    def validate(self, attrs):
        instance = self.instance

        name = attrs.get("name", getattr(instance, "name", None))
        code = attrs.get("code", getattr(instance, "code", None))

        # Duplicate name check
        name_qs = Menu.objects.filter(name__iexact=name, status=True)
        if instance:
            name_qs = name_qs.exclude(pk=instance.pk)
        if name_qs.exists():
            raise serializers.ValidationError({"name": f"Menu with name '{name}' already exists."})

        # Duplicate code check
        code_qs = Menu.objects.filter(code=code, status=True)
        if instance:
            code_qs = code_qs.exclude(pk=instance.pk)
        if code_qs.exists():
            raise serializers.ValidationError({"code": f"Menu with code '{code}' already exists."})

        return attrs