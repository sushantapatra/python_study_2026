"""
core/models.py — BaseModel

Yeh ek abstract model hai.
Abstract matlab: iska khud ka koi database table nahi banega.
Sirf inherit karne ke liye hai — jo bhi model isse inherit karega
uske table mein automatically yeh saare fields aa jayenge.

Laravel Style Soft Delete:
- `is_deleted` flag ko hata diya gaya hai.
- `deleted_at` (null/not null) se pata chalta hai record active hai ya deleted.
- `delete()` method ko override kiya hai taki by default soft delete ho.
"""

from django.db import models
from django.utils import timezone
from core.managers import SoftDeleteManager

class BaseModel(models.Model):
    """
    Abstract base model — saare project models isse inherit karenge.

    Audit fields:
        created_by  → kisne create kiya (User ka FK)
        updated_by  → kisne last update kiya
        deleted_by  → kisne soft delete kiya

    Timestamp fields:
        created_at  → kab create hua (auto set on INSERT)
        updated_at  → kab last update hua (auto set on UPDATE)
        deleted_at  → kab soft delete hua (None = active record)
    """

    # ── Audit: kisne kiya ──────────────────────────────────────
    # String reference "users.User" use kiya hai circular import se bachne ke liye
    created_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_created",
        db_column="created_by",
    )
    updated_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_updated",
        db_column="updated_by",
    )
    deleted_by = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(app_label)s_%(class)s_deleted",
        db_column="deleted_by",
    )

    # ── Timestamps: kab hua ───────────────────────────────────
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_column="created_at",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_column="updated_at",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_column="deleted_at",
    )

    # Managers
    objects = SoftDeleteManager()
    all_objects = models.Manager()  # Plain manager for internal use if needed

    class Meta:
        abstract = True

    @property
    def is_deleted(self):
        """Backward compatibility ke liye is_deleted property."""
        return self.deleted_at is not None

    def delete(self, *args, **kwargs):
        """
        Default delete behaviour: Soft Delete.
        Agar `force=True` pass karenge to permanently delete hoga.
        """
        force = kwargs.pop('force', False)
        deleted_by_user = kwargs.pop('deleted_by', None)

        if force:
            return super().delete(*args, **kwargs)

        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by_user
        self.save(update_fields=["deleted_at", "deleted_by"])

    def restore(self):
        """Soft deleted record ko wapas active karo."""
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["deleted_at", "deleted_by"])

    def hard_delete(self, *args, **kwargs):
        """Permanently delete record."""
        return super().delete(*args, **kwargs)
