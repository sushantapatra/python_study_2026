"""
users/serializers/auth_serializer.py

Auth ke liye serializers:
    RegisterSerializer      → naya user banao
    LoginSerializer         → email + password validate karo
    UserProfileSerializer   → profile output
    ProfileUpdateSerializer → profile update
    ChangePasswordSerializer → password change
    ForgotPasswordSerializer → email se OTP/link bhejo
    ResetPasswordSerializer  → naya password set karo
"""

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from users.models import User


# ── Output ─────────────────────────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    """Read-only — profile response mein use hota hai."""

    role_name = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            "id", "first_name", "last_name", "full_name",
            "email", "avatar_url", "bio", "phone",
            "role", "role_name",
            "is_active", "is_email_verified",
            "last_login", "created_at",
        ]

    def get_role_name(self, obj):
        return obj.role.name if obj.role else None

    def get_full_name(self, obj):
        return obj.get_full_name()


# ── Register ───────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    """
    New user registration.

    Validations:
        1. DRF default (required, email format, max_length)
        2. Email duplicate: Active (non-deleted) users mein check karo.
        3. Password: Django's built-in validators
        4. confirm_password: password match
    """

    confirm_password = serializers.CharField(write_only=True, required=True)
    password         = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model  = User
        fields = ["first_name", "last_name", "email", "password", "confirm_password", "phone"]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name":  {"required": True},
            "email":      {"required": True},
        }

    def validate_first_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("First name cannot be blank.")
        if len(value) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters.")
        if not value.replace(" ", "").isalpha():
            raise serializers.ValidationError("First name can only contain letters.")
        return value

    def validate_last_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Last name cannot be blank.")
        if len(value) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters.")
        if not value.replace(" ", "").isalpha():
            raise serializers.ValidationError("Last name can only contain letters.")
        return value

    def validate_email(self, value):
        value = value.strip().lower()
        # Duplicate check: active + non-deleted users mein
        if User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError(
                "An account with this email already exists."
            )
        return value

    def validate_password(self, value):
        """Django's built-in password validators use karo."""
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        # Default role: subscriber (seed data mein hoga)
        from users.models import Role
        default_role = Role.objects.filter(code="subscriber").first()

        user = User.objects.create_user(
            email      = validated_data["email"],
            password   = validated_data["password"],
            first_name = validated_data["first_name"],
            last_name  = validated_data["last_name"],
            phone      = validated_data.get("phone", ""),
            role       = default_role,
        )
        return user


# ── Login ──────────────────────────────────────────────────────────────────

class LoginSerializer(serializers.Serializer):
    """
    Email + password login.

    Checks:
        1. Email aur password required
        2. User exist karta hai (active + non-deleted)
        3. Password correct hai
        4. Account active hai
    """

    email    = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email    = attrs.get("email", "").strip().lower()
        password = attrs.get("password", "")

        # User exist karta hai?
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError(
                {"email": "No active account found with this email."}
            )

        # Account active hai?
        if not user.is_active:
            raise serializers.ValidationError(
                {"email": "Your account has been deactivated. Please contact support."}
            )

        # Password correct hai?
        if not user.check_password(password):
            raise serializers.ValidationError(
                {"password": "Incorrect password. Please try again."}
            )

        attrs["user"] = user
        return attrs


# ── Profile Update ─────────────────────────────────────────────────────────

class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Profile update — email aur password is serializer se nahi badlenge.
    Unke liye alag APIs hain (security ke liye).
    """

    class Meta:
        model  = User
        fields = ["first_name", "last_name", "phone", "bio", "avatar_url"]

    def validate_first_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("First name cannot be blank.")
        if len(value) < 2:
            raise serializers.ValidationError("First name must be at least 2 characters.")
        return value

    def validate_last_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Last name cannot be blank.")
        if len(value) < 2:
            raise serializers.ValidationError("Last name must be at least 2 characters.")
        return value


# ── Change Password ────────────────────────────────────────────────────────

class ChangePasswordSerializer(serializers.Serializer):
    """
    Logged-in user apna password change kare.
    Current password verify karta hai — security ke liye.
    """

    current_password = serializers.CharField(required=True, write_only=True)
    new_password     = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs


# ── Forgot Password ────────────────────────────────────────────────────────

class ForgotPasswordSerializer(serializers.Serializer):
    """
    Email se password reset link/OTP bhejo.
    Email exist nahi karta? Phir bhi same message dikhao — security.
    """

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        return value.strip().lower()


# ── Reset Password ─────────────────────────────────────────────────────────

class ResetPasswordSerializer(serializers.Serializer):
    """
    Token + new password se reset karo.
    Token → forgot password ke time generate hua tha.
    """

    token            = serializers.CharField(required=True)
    new_password     = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs