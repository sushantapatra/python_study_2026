"""
users/serializers/action_serializer.py
"""

from rest_framework import serializers
from users.models import Action


class ActionOutputSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    deleted_by = serializers.SerializerMethodField()

    class Meta:
        model  = Action
        fields = [
            "id",
            "name",
            "code",
            "description",
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


class ActionInputSerializer(serializers.ModelSerializer):

    class Meta:
        model  = Action
        fields = ["name", "code", "description", "status"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Action name cannot be blank.")
        if len(value) < 2:
            raise serializers.ValidationError("Action name must be at least 2 characters.")
        return value

    def validate_code(self, value):
        value = value.strip().lower().replace(" ", "_").replace("-", "_")
        if not value:
            raise serializers.ValidationError("Action code cannot be blank.")
        if not re.match(r'^[a-z0-9_]+$', value):
            raise serializers.ValidationError(
                "Action code can only contain lowercase letters, numbers, and underscores."
            )
        return value

    def validate(self, attrs):
        instance = self.instance

        name = attrs.get("name", getattr(instance, "name", None))
        code = attrs.get("code", getattr(instance, "code", None))

        name_qs = Action.objects.filter(name__iexact=name, status=True)
        if instance:
            name_qs = name_qs.exclude(pk=instance.pk)
        if name_qs.exists():
            raise serializers.ValidationError({"name": f"Action with name '{name}' already exists."})

        code_qs = Action.objects.filter(code=code, status=True)
        if instance:
            code_qs = code_qs.exclude(pk=instance.pk)
        if code_qs.exists():
            raise serializers.ValidationError({"code": f"Action with code '{code}' already exists."})

        return attrs