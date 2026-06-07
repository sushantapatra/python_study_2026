"""
users/serializers/role_serializer.py

Role ke liye serializers.

Kyun do alag serializers (Input aur Output)?
    Input  (RoleInputSerializer):
        - Sirf wo fields jo user bhejta hai (name, code, description, status)
        - Validation yahan hoti hai
        - Write-only fields

    Output (RoleOutputSerializer):
        - Jo user ko response mein milta hai
        - Extra fields: created_by name, created_at etc.
        - Read-only

Yeh approach "Single Responsibility" follow karta hai —
input validate karna aur output format karna alag kaam hai.
"""

from rest_framework import serializers
from users.models import Role


class RoleOutputSerializer(serializers.ModelSerializer):
    """
    Response mein Role data kaisa dikhega.
    created_by → user ka naam (id nahi)
    """

    created_by = serializers.SerializerMethodField()
    updated_by = serializers.SerializerMethodField()
    deleted_by = serializers.SerializerMethodField()

    class Meta:
        model  = Role
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


class RoleInputSerializer(serializers.ModelSerializer):
    """
    Create / Update ke liye input validation.

    Validations:
        1. name aur code required hain
        2. code automatically lowercase + underscore format mein convert hoga
        3. Duplicate name check (active records mein)
        4. Duplicate code check (active records mein)
    """

    class Meta:
        model  = Role
        fields = ["name", "code", "description", "status"]
        extra_kwargs = {
            "name":   {"required": True},
            "code":   {"required": True},
            "status": {"required": False, "default": True},
        }

    def validate_name(self, value):
        """Name: strip whitespace, empty nahi hona chahiye."""
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Role name cannot be blank.")
        if len(value) < 2:
            raise serializers.ValidationError("Role name must be at least 2 characters.")
        if len(value) > 100:
            raise serializers.ValidationError("Role name cannot exceed 100 characters.")
        return value

    def validate_code(self, value):
        """
        Code: lowercase, spaces ko underscore se replace karo.
        'Super Admin' → 'super_admin'
        """
        value = value.strip().lower().replace(" ", "_").replace("-", "_")
        if not value:
            raise serializers.ValidationError("Role code cannot be blank.")
        if len(value) > 100:
            raise serializers.ValidationError("Role code cannot exceed 100 characters.")
        # Sirf alphanumeric aur underscore allowed
        import re
        if not re.match(r'^[a-z0-9_]+$', value):
            raise serializers.ValidationError(
                "Role code can only contain lowercase letters, numbers, and underscores."
            )
        return value

    def validate(self, attrs):
        """
        Cross-field validation — duplicate check.

        self.instance:
            None     → Create operation (POST)
            <object> → Update operation (PUT/PATCH)

        Update mein apna hi record exclude karte hain duplicate check se.
        """
        instance = self.instance  # None for create, Role object for update

        name = attrs.get("name", getattr(instance, "name", None))
        code = attrs.get("code", getattr(instance, "code", None))

        # Duplicate name: active + non-deleted records mein
        name_qs = Role.objects.filter(
            name__iexact=name,
            status=True,
        )

        if instance:
            name_qs = name_qs.exclude(pk=instance.pk)
        if name_qs.exists():
            raise serializers.ValidationError({"name": f"Role with name '{name}' already exists."})


        # Duplicate code: active + non-deleted records mein
        code_qs = Role.objects.filter(
            code=code,
            status=True,
        )
        if instance:
            code_qs = code_qs.exclude(pk=instance.pk)
        if code_qs.exists():
            raise serializers.ValidationError({"code": f"Role with code '{code}' already exists."})

        return attrs