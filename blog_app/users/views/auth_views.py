"""
users/views/auth_views.py

Authentication APIs — complete flow.

Permission rules (tumhara requirement):
    - Login, Register, Forgot Password, Reset Password → AllowAny
    - Logout, Logout All, Refresh Token              → IsAuthenticatedActive
    - Profile (view/update), Change Password         → IsAuthenticatedActive

Har API pe ActivityLog hoga.
"""

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from drf_spectacular.utils import extend_schema

from core.response import success_response, error_response
from core.utils    import log_activity
from users.models  import User, PasswordResetToken
from users.permissions import IsAuthenticatedActive
from users.serializers.auth_serializer import (
    RegisterSerializer,
    LoginSerializer,
    UserProfileSerializer,
    ProfileUpdateSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)


# ── Helper ──────────────────────────────────────────────────────────────────

def get_tokens_for_user(user):
    """
    User ke liye JWT access + refresh token generate karo.
    SimpleJWT ka RefreshToken class use karo.
    """
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access":  str(refresh.access_token),
    }


# ── Register ────────────────────────────────────────────────────────────────

class RegisterView(APIView):
    """
    POST /api/v1/auth/register/
    Permission: AllowAny — koi bhi register kar sakta hai
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Register new user",
        request=RegisterSerializer,
        responses={201: UserProfileSerializer},
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Registration failed. Please fix the errors.",
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        tokens = get_tokens_for_user(user)

        log_activity(
            request=request,
            user=user,
            model_name="User",
            action_name="register",
            object_id=user.id,
            after_input={"email": user.email, "name": user.get_full_name()},
            description=f"New user registered: {user.email}",
        )

        return success_response(
            data={
                "user":   UserProfileSerializer(user).data,
                "tokens": tokens,
            },
            message="Registration successful. Welcome to Tech Blog!",
            status=status.HTTP_201_CREATED,
        )


# ── Login ────────────────────────────────────────────────────────────────────

class LoginView(APIView):
    """
    POST /api/v1/auth/login/
    Permission: AllowAny
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Login",
        request=LoginSerializer,
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            # Failed login bhi log karo
            log_activity(
                request=request,
                model_name="User",
                action_name="login_failed",
                description=f"Failed login attempt for: {request.data.get('email', '')}",
            )
            return error_response(
                message="Login failed. Please check your credentials.",
                errors=serializer.errors,
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = serializer.validated_data["user"]

        # last_login update karo
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        tokens = get_tokens_for_user(user)

        log_activity(
            request=request,
            user=user,
            model_name="User",
            action_name="login",
            object_id=user.id,
            description=f"User logged in: {user.email}",
        )

        return success_response(
            data={
                "user":   UserProfileSerializer(user).data,
                "tokens": tokens,
            },
            message="Login successful.",
        )


# ── Logout ───────────────────────────────────────────────────────────────────

class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    Permission: IsAuthenticatedActive
    Body: {"refresh": "<refresh_token>"}

    Current session ka refresh token blacklist karo.
    """

    permission_classes = [IsAuthenticatedActive]

    @extend_schema(
        summary="Logout (current session)",
        request={"application/json": {"type": "object", "properties": {
            "refresh": {"type": "string"}
        }, "required": ["refresh"]}},
        tags=["Authentication"],
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return error_response(
                message="Refresh token is required.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return error_response(
                message="Invalid or already expired token.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        log_activity(
            request=request,
            user=request.user,
            model_name="User",
            action_name="logout",
            object_id=request.user.id,
            description=f"User logged out: {request.user.email}",
        )

        return success_response(message="Logged out successfully.")


# ── Logout All Sessions ───────────────────────────────────────────────────────

class LogoutAllView(APIView):
    """
    POST /api/v1/auth/logout-all/
    Permission: IsAuthenticatedActive

    User ke saare outstanding tokens blacklist karo.
    (All sessions logout — sab devices se)
    """

    permission_classes = [IsAuthenticatedActive]

    @extend_schema(
        summary="Logout from all sessions",
        tags=["Authentication"],
    )
    def post(self, request):
        # User ke sab outstanding (non-blacklisted) tokens lo
        tokens = OutstandingToken.objects.filter(user=request.user)
        count  = 0
        for token in tokens:
            # Already blacklisted nahi hai to blacklist karo
            if not BlacklistedToken.objects.filter(token=token).exists():
                BlacklistedToken.objects.create(token=token)
                count += 1

        log_activity(
            request=request,
            user=request.user,
            model_name="User",
            action_name="logout_all",
            object_id=request.user.id,
            description=f"User logged out from all sessions ({count} sessions): {request.user.email}",
        )

        return success_response(
            message=f"Logged out from all {count} active session(s)."
        )


# ── Token Refresh ─────────────────────────────────────────────────────────────

class TokenRefreshView(APIView):
    """
    POST /api/v1/auth/token/refresh/
    Permission: AllowAny (token hi credential hai)
    Body: {"refresh": "<refresh_token>"}

    Naya access token lo bina re-login ke.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Refresh access token",
        request={"application/json": {"type": "object", "properties": {
            "refresh": {"type": "string"}
        }, "required": ["refresh"]}},
        tags=["Authentication"],
    )
    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return error_response(
                message="Refresh token is required.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token  = RefreshToken(refresh_token)
            # ROTATE_REFRESH_TOKENS=True → naya refresh token bhi milega
            new_access   = str(token.access_token)
            new_refresh  = str(token)
        except TokenError as e:
            return error_response(
                message="Invalid or expired refresh token. Please login again.",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return success_response(
            data={"access": new_access, "refresh": new_refresh},
            message="Token refreshed successfully.",
        )


# ── Profile ───────────────────────────────────────────────────────────────────

class ProfileView(APIView):
    """
    GET  /api/v1/auth/profile/        → apna profile dekho
    POST /api/v1/auth/profile/update/ → profile update karo
    Permission: IsAuthenticatedActive
    """

    permission_classes = [IsAuthenticatedActive]

    @extend_schema(
        summary="Get my profile",
        responses={200: UserProfileSerializer},
        tags=["Profile"],
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return success_response(data=serializer.data)


class ProfileUpdateView(APIView):
    """POST /api/v1/auth/profile/update/"""

    permission_classes = [IsAuthenticatedActive]

    @extend_schema(
        summary="Update my profile",
        request=ProfileUpdateSerializer,
        responses={200: UserProfileSerializer},
        tags=["Profile"],
    )
    def post(self, request):
        # before snapshot for activity log
        before = {
            "first_name": request.user.first_name,
            "last_name":  request.user.last_name,
            "phone":      request.user.phone,
            "bio":        request.user.bio,
        }

        serializer = ProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        if not serializer.is_valid():
            return error_response(
                message="Validation failed.",
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()

        log_activity(
            request=request,
            user=user,
            model_name="User",
            action_name="profile_update",
            object_id=user.id,
            before_input=before,
            after_input={
                "first_name": user.first_name,
                "last_name":  user.last_name,
                "phone":      user.phone,
            },
            description=f"Profile updated: {user.email}",
        )

        return success_response(
            data=UserProfileSerializer(user).data,
            message="Profile updated successfully.",
        )


# ── Change Password ───────────────────────────────────────────────────────────

class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/
    Permission: IsAuthenticatedActive
    """

    permission_classes = [IsAuthenticatedActive]

    @extend_schema(
        summary="Change password",
        request=ChangePasswordSerializer,
        tags=["Profile"],
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation failed.",
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Current password verify karo
        if not request.user.check_password(serializer.validated_data["current_password"]):
            return error_response(
                message="Current password is incorrect.",
                errors={"current_password": "Incorrect password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Naya password set karo
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save(update_fields=["password"])

        # All other sessions invalidate karo (security)
        tokens = OutstandingToken.objects.filter(user=request.user)
        for token in tokens:
            if not BlacklistedToken.objects.filter(token=token).exists():
                BlacklistedToken.objects.create(token=token)

        log_activity(
            request=request,
            user=request.user,
            model_name="User",
            action_name="change_password",
            object_id=request.user.id,
            description=f"Password changed: {request.user.email}",
        )

        return success_response(
            message="Password changed successfully. Please login again with your new password."
        )


# ── Forgot Password ───────────────────────────────────────────────────────────

class ForgotPasswordView(APIView):
    """
    POST /api/v1/auth/forgot-password/
    Permission: AllowAny

    Email bhejo → token generate karo → email send karo.
    Security: email exist na kare to bhi same message dikhao.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Forgot password — send reset link",
        request=ForgotPasswordSerializer,
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation failed.",
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"]

        # User exist karta hai? Silently handle karo (security)
        try:
            user = User.objects.get(email=email, is_active=True)
            token_obj = PasswordResetToken.create_for_user(user)

            # TODO: Email send karo — Step email integration mein
            # send_password_reset_email(user, token_obj.token)

            log_activity(
                request=request,
                user=user,
                model_name="User",
                action_name="forgot_password",
                object_id=user.id,
                description=f"Password reset requested: {email}",
            )
        except User.DoesNotExist:
            # Security: same response dono cases mein
            log_activity(
                request=request,
                model_name="User",
                action_name="forgot_password_attempt",
                description=f"Password reset attempted for unknown email: {email}",
            )

        # Dono cases mein same response (email enumeration prevent karo)
        return success_response(
            message="If an account exists with this email, you will receive a password reset link shortly."
        )


# ── Reset Password ────────────────────────────────────────────────────────────

class ResetPasswordView(APIView):
    """
    POST /api/v1/auth/reset-password/
    Permission: AllowAny
    Body: {"token": "...", "new_password": "...", "confirm_password": "..."}
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="Reset password with token",
        request=ResetPasswordSerializer,
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Validation failed.",
                errors=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        token_str = serializer.validated_data["token"]

        try:
            token_obj = PasswordResetToken.objects.select_related("user").get(
                token=token_str
            )
        except PasswordResetToken.DoesNotExist:
            return error_response(
                message="Invalid or expired password reset token.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not token_obj.is_valid():
            return error_response(
                message="This password reset link has expired or already been used.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = token_obj.user

        # Naya password set karo
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])

        # Token use mark karo
        token_obj.is_used = True
        token_obj.save(update_fields=["is_used"])

        # All sessions logout karo
        tokens = OutstandingToken.objects.filter(user=user)
        for t in tokens:
            if not BlacklistedToken.objects.filter(token=t).exists():
                BlacklistedToken.objects.create(token=t)

        log_activity(
            request=request,
            user=user,
            model_name="User",
            action_name="reset_password",
            object_id=user.id,
            description=f"Password reset successful: {user.email}",
        )

        return success_response(
            message="Password reset successful. Please login with your new password."
        )