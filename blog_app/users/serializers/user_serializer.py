"""
users/serializers/user_serializer.py

User ke liye serializers:
    UserOutputSerializer    → Profile response
    RegisterSerializer      → New user registration
    ProfileUpdateSerializer → Profile update (naam, bio, avatar)
"""

import re
from rest_framework import serializers
from users.models import User, Role


class UserOutputSerializer(serializers.ModelSerializer):
    """Profile response — password kabhi return nahi hoga."""

    role_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            "id", "first_name", "last_name", "full_name",
            "email", "phone", "bio", "avatar_url",
            "role", "role_name",
            "is_active", "is_email_verified",
            "last_login", "created_at", "updated_at",
        ]

    def get_role_name(self, obj):
        return obj.role.name if obj.role else None

    def get_full_name(self, obj):
        return obj.get_full_name()


class RegisterSerializer(serializers.ModelSerializer):
    """
    New user registration.

    Validation:
        first_name  : Required, 2-50 chars, letters only
        last_name   : Required, 2-50 chars, letters only
        email       : Required, valid format, unique (active users mein)
        password    : Required, min 8 chars, must have uppercase + digit + special char
        confirm_password : Must match password
        role        : Optional FK — active role hona chahiye
        phone       : Optional, basic format check
    """

    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model  = User
        fields = [
            "first_name", "last_name", "email",
            "password", "confirm_password",
            "phone", "role",
        ]
        extra_kwargs = {
            "password": {"write_only": True, "min_length": 8},
            "phone":    {"required": False, "allow_blank": True, "allow_null": True},
            "role":     {"required": False, "allow_null": True},
        }

    def validate_first_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("First name cannot be blank.")
        if len(value) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters.")
        if len(value) > 50:
            raise serializers.ValidationError("First name cannot exceed 50 characters.")
        if not re.match(r"^[a-zA-Z\s\-']+$", value):
            raise serializers.ValidationError(
                "First name can only contain letters, spaces, hyphens, and apostrophes."
            )
        return value

    def validate_last_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Last name cannot be blank.")
        if len(value) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters.")
        if len(value) > 50:
            raise serializers.ValidationError("Last name cannot exceed 50 characters.")
        if not re.match(r"^[a-zA-Z\s\-']+$", value):
            raise serializers.ValidationError(
                "Last name can only contain letters, spaces, hyphens, and apostrophes."
            )
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        if not value:
            raise serializers.ValidationError("Email cannot be blank.")
        # Active users mein duplicate check
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters.")
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )
        if not re.search(r"\d", value):
            raise serializers.ValidationError(
                "Password must contain at least one digit."
            )
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise serializers.ValidationError(
                "Password must contain at least one special character."
            )
        return value

    def validate_phone(self, value):
        if not value:
            return value
        # Basic phone format: optional +, then digits, spaces, hyphens
        cleaned = re.sub(r"[\s\-\(\)]", "", value)
        if not re.match(r"^\+?\d{7,15}$", cleaned):
            raise serializers.ValidationError(
                "Enter a valid phone number (7-15 digits, optional + prefix)."
            )
        return value

    def validate_role(self, value):
        if value is None:
            return value
        if value.is_deleted:
            raise serializers.ValidationError("Selected role is deleted.")
        if not value.status:
            raise serializers.ValidationError("Selected role is inactive.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)   # hash karo
        user.save()
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Profile update — sirf safe fields.
    Email/password change ke liye alag endpoints hain.
    """

    class Meta:
        model  = User
        fields = ["first_name", "last_name", "phone", "bio", "avatar_url"]
        extra_kwargs = {
            "first_name": {"required": False},
            "last_name":  {"required": False},
            "phone":      {"required": False, "allow_blank": True, "allow_null": True},
            "bio":        {"required": False, "allow_blank": True, "allow_null": True},
            "avatar_url": {"required": False, "allow_blank": True, "allow_null": True},
        }

    def validate_first_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("First name cannot be blank.")
        if len(value) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters.")
        if len(value) > 50:
            raise serializers.ValidationError("First name cannot exceed 50 characters.")
        if not re.match(r"^[a-zA-Z\s\-']+$", value):
            raise serializers.ValidationError(
                "First name can only contain letters, spaces, hyphens, and apostrophes."
            )
        return value

    def validate_last_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Last name cannot be blank.")
        if len(value) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters.")
        if len(value) > 50:
            raise serializers.ValidationError("Last name cannot exceed 50 characters.")
        if not re.match(r"^[a-zA-Z\s\-']+$", value):
            raise serializers.ValidationError(
                "Last name can only contain letters, spaces, hyphens, and apostrophes."
            )
        return value

    def validate_bio(self, value):
        if value and len(value) > 1000:
            raise serializers.ValidationError("Bio cannot exceed 1000 characters.")
        return value

    def validate_phone(self, value):
        if not value:
            return value
        cleaned = re.sub(r"[\s\-\(\)]", "", value)
        if not re.match(r"^\+?\d{7,15}$", cleaned):
            raise serializers.ValidationError(
                "Enter a valid phone number (7-15 digits, optional + prefix)."
            )
        return value