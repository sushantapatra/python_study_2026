"""
users/models/password_reset.py

PasswordResetToken — forgot password flow ke liye.

Flow:
    1. User → POST /forgot-password/ → {email}
    2. System → token generate karo, DB mein save karo, email bhejo
    3. User → POST /reset-password/ → {token, new_password}
    4. System → token valid hai? → password change karo, token delete karo

Security:
    - Token: secrets.token_urlsafe(32) → cryptographically secure
    - expires_at: 1 ghante mein expire
    - is_used: ek baar use hone ke baad invalidate
"""

from django.db import models
from django.utils import timezone
import secrets


class PasswordResetToken(models.Model):
    user       = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token      = models.CharField(max_length=128, unique=True, db_index=True)
    expires_at = models.DateTimeField()
    is_used    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "password_reset_tokens"
        ordering = ["-created_at"]

    @classmethod
    def create_for_user(cls, user):
        """
        User ke liye naya token banao.
        Purane unused tokens delete karo (cleanup).
        """
        # Purane tokens delete karo
        cls.objects.filter(user=user, is_used=False).delete()

        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timezone.timedelta(hours=1)
        return cls.objects.create(user=user, token=token, expires_at=expires_at)

    def is_valid(self):
        """Token valid hai? (not used + not expired)"""
        return not self.is_used and self.expires_at > timezone.now()

    def __str__(self):
        return f"ResetToken for {self.user.email}"