"""
core/models.py — BaseModel

Yeh ek abstract model hai.
Abstract matlab: iska khud ka koi database table nahi banega.
Sirf inherit karne ke liye hai — jo bhi model isse inherit karega
uske table mein automatically yeh saare fields aa jayenge.

Kyun yeh approach?
- DRY principle: ek jagah likho, sab jagah kaam aaye
- Consistency: har table mein same audit fields honge
- Soft delete: data permanently delete nahi hoga

Usage:
    class Role(BaseModel):
        name = models.CharField(max_length=100)
        # Role table mein automatically milega:
        # created_at, created_by, updated_at, updated_by,
        # deleted_at, deleted_by, is_deleted
"""

from django.db import models


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

    Soft delete:
        is_deleted  → True = deleted, False = active
        deleted_at  → deletion timestamp

    Note: created_by, updated_by, deleted_by ko
    circular import se bachne ke liye string reference se define kiya hai:
    "users.User" → Django runtime pe resolve karega
    null=True, blank=True → creation ke time user available nahi hota
    (jaise system-generated records)
    """

    # ── Audit: kisne kiya ──────────────────────────────────────
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
        auto_now_add=True,   # INSERT ke time automatically set hoga
        db_column="created_at",
    )
    updated_at = models.DateTimeField(
        auto_now=True,       # har UPDATE pe automatically set hoga
        db_column="updated_at",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_column="deleted_at",
    )

    # ── Soft Delete flag ──────────────────────────────────────
    is_deleted = models.BooleanField(
        default=False,
        db_column="is_deleted",
    )

    class Meta:
        abstract = True   # ← yahi key hai — koi table nahi banega

    def soft_delete(self, deleted_by_user=None):
        """
        Record ko permanently delete nahi karta.
        Sirf is_deleted=True aur deleted_at set karta hai.

        Usage:
            role.soft_delete(deleted_by_user=request.user)
        """
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by_user
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])

    def restore(self):
        """
        Soft deleted record ko wapas active karo.

        Usage:
            role.restore()
        """
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by"])