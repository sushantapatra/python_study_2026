"""
users/models/user.py — Custom User Model

Kyun Django ka default User nahi use kar rahe?
1. Default User mein username required hai — hum email se login karenge
2. Default User mein bio, avatar, role jaisi fields nahi hain
3. Ek baar project chal jaaye phir default User change karna bahut mushkil hota hai
   — isliye shuruaat se hi khud ka banao

AbstractBaseUser:
    - Sirf password hashing aur authentication logic deta hai
    - Baaki sab hum define karte hain (email, name, etc.)
    - Yeh sab se flexible approach hai

PermissionsMixin:
    - Django ka built-in groups aur permissions system deta hai
    - is_superuser, user_permissions, groups fields aate hain
    - Django Admin ke saath kaam karne ke liye zaroori hai

UserManager:
    - create_user() aur create_superuser() commands ke liye
    - python manage.py createsuperuser isi se kaam karta hai
"""

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    Custom manager — email se user create karne ke liye.
    Django ka default manager username use karta hai.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        Normal user create karo.
        extra_fields mein first_name, last_name etc. pass kar sakte hain.
        """
        if not email:
            raise ValueError("Email field is required.")
        email = self.normalize_email(email)   # lowercase domain part
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)           # password hash karega
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Superuser create karo — manage.py createsuperuser isko call karta hai.
        """
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

    Note: Yeh model BaseModel se inherit NAHI karta.
    Kyun? BaseModel mein created_by = FK("users.User") hai.
    Agar User model bhi BaseModel se inherit kare to
    circular dependency ho jaayegi: User → User → User...

    Isliye User mein manually created_at, updated_at rakhe hain.
    Soft delete bhi manually define kiya hai.
    """

    # ── Identity ──────────────────────────────────────────────
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    email      = models.EmailField(unique=True)   # login ke liye

    # ── Profile ───────────────────────────────────────────────
    avatar_url = models.URLField(
        max_length=500,
        null=True,
        blank=True,
    )
    bio = models.TextField(
        null=True,
        blank=True,
    )
    phone = models.CharField(
        max_length=20,
        null=True,
        blank=True,
    )

    # ── Role (FK) ─────────────────────────────────────────────
    # null=True: Role app baad mein banega (Step 5)
    # settings.py mein AUTH_USER_MODEL set hone ke baad
    # Role aur User ek dusre ko refer kar sakte hain
    role = models.ForeignKey(
        "roles.Role",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
        db_column="role_id",
    )

    # ── Django Required Fields ────────────────────────────────
    is_active       = models.BooleanField(default=True)
    is_staff        = models.BooleanField(default=False)   # Django admin access
    is_email_verified = models.BooleanField(default=False)

    # ── Timestamps ────────────────────────────────────────────
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── Soft Delete ───────────────────────────────────────────
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        "self",                        # User ne User ko delete kiya
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deleted_users",
        db_column="deleted_by",
    )

    # ── Manager ───────────────────────────────────────────────
    objects = UserManager()

    # ── Auth Configuration ────────────────────────────────────
    USERNAME_FIELD  = "email"          # login mein email use hogi
    REQUIRED_FIELDS = ["first_name", "last_name"]  # createsuperuser prompt

    class Meta:
        db_table  = "users"
        ordering  = ["-created_at"]
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(fields=["email"],      name="idx_users_email"),
            models.Index(fields=["is_deleted"], name="idx_users_is_deleted"),
            models.Index(fields=["role"],       name="idx_users_role"),
        ]

    def __str__(self):
        return f"{self.get_full_name()} <{self.email}>"

    # ── Helper Methods ────────────────────────────────────────
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_short_name(self):
        return self.first_name

    def soft_delete(self, deleted_by_user=None):
        """User ko permanently delete nahi karte — sirf mark karte hain."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by_user
        self.is_active  = False
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "is_active"])

    def restore(self):
        """Soft deleted user ko wapas active karo."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.is_active  = True
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "is_active"])