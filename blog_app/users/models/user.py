"""
users/models/user.py — Custom User Model

Note: User model BaseModel se inherit nahi karta circular import ki wajah se.
Lekin hum isme Laravel style soft delete implement kar rahe hain.
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from .role import Role


class UserManager(BaseUserManager):
    """
    Custom manager — email se user create karne ke liye.
    Soft delete aware manager.
    """

    def get_queryset(self):
        """By default sirf active (non-deleted) users dikhao."""
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        """Deleted users ke saath results chahiye to isko call karo."""
        return super().get_queryset()

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email field is required.")
        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model.
    """

    # ── Identity ──────────────────────────────────────────────
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    email      = models.EmailField(unique=True)

    # ── Profile ───────────────────────────────────────────────
    avatar_url = models.URLField(max_length=500, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)

    # ── Role (FK) ─────────────────────────────────────────────
    role = models.ForeignKey(
        Role,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
        db_column="role_id",
    )

    # ── Django Required Fields ────────────────────────────────
    is_active       = models.BooleanField(default=True)
    is_staff        = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    # ── Timestamps ────────────────────────────────────────────
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── Soft Delete (Laravel Style) ───────────────────────────
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deleted_users",
        db_column="deleted_by",
    )

    # ── Manager ───────────────────────────────────────────────
    objects = UserManager()

    # ── Auth Configuration ────────────────────────────────────
    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table  = "users"
        ordering  = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["email"],      name="idx_users_email"),
            models.Index(fields=["deleted_at"], name="idx_users_deleted_at"),
            models.Index(fields=["role"],       name="idx_users_role"),
        ]

    @property
    def is_deleted(self):
        """Backward compatibility ke liye is_deleted property."""
        return self.deleted_at is not None

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def delete(self, *args, **kwargs):
        """Soft delete user by default."""
        force = kwargs.pop('force', False)
        deleted_by_user = kwargs.pop('deleted_by', None)

        if force:
            return super().delete(*args, **kwargs)

        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by_user
        self.is_active  = False
        self.save(update_fields=["deleted_at", "deleted_by", "is_active"])

    def restore(self):
        """Soft deleted user ko wapas active karo."""
        self.deleted_at = None
        self.deleted_by = None
        self.is_active  = True
        self.save(update_fields=["deleted_at", "deleted_by", "is_active"])
