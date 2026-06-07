"""
core/managers.py — Custom QuerySet Managers

Problem jo solve ho raha hai:
    Har jagah manually `deleted_at__isnull=True` likhna padta tha.
    Agar ek jagah bhi bhool gaye → deleted records dikh jaate.

Solution (Laravel style):
    SoftDeleteManager → by default sirf active records (deleted_at IS NULL) return karta hai.
    `with_deleted()` manager method → deleted records bhi chahiye to yeh use karo.

Usage in models:
    class Role(BaseModel):
        objects = SoftDeleteManager()

    Role.objects.all()              → sirf active records
    Role.objects.only_deleted()      → sirf soft-deleted records
    Role.objects.with_deleted()      → sab records
"""

from django.db import models
from django.utils import timezone

class SoftDeleteQuerySet(models.QuerySet):
    """
    Custom QuerySet jo soft delete operations handle karta hai.
    """

    def delete(self):
        """Batch soft delete — model.delete() ki jagah update() use karega."""
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        """Records ko permanently database se delete karne ke liye."""
        return super().delete()

    def restore(self):
        """Soft deleted records ko wapas active karne ke liye."""
        return super().update(deleted_at=None)

    def active(self):
        """Sirf active records (deleted_at is null)."""
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        """Sirf soft-deleted records (deleted_at is not null)."""
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    """
    Default manager — automatically active records filter lagata hai.
    Matlab Model.objects.all() mein deleted records kabhi nahi aayenge.
    """

    def get_queryset(self):
        """Default: sirf active records dikhao."""
        return SoftDeleteQuerySet(self.model, using=self._db).active()

    def with_deleted(self):
        """Sab records access karne ke liye (Active + Deleted)."""
        return SoftDeleteQuerySet(self.model, using=self._db)

    def only_deleted(self):
        """Sirf soft-deleted records dekhne ke liye."""
        return SoftDeleteQuerySet(self.model, using=self._db).deleted()

    def restore(self):
        """Deleted records ko bulk restore karne ke liye."""
        return self.only_deleted().restore()
