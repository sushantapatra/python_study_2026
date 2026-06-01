# core/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from core.middleware import get_current_thread_user

class ActiveManager(models.Manager):
    """ Custom manager to automatically filter out soft-deleted entries across queries. """
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class BaseModel(models.Model):
    """
    SOLID Principle: Single Responsibility.
    Abstract architecture containing tracking fields and soft-deletion controls.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created_records"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_updated_records"
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_deleted_records"
    )

    # Managers assignment
    objects = ActiveManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        current_user = get_current_thread_user()
        
        if not self.pk:
            # Creation phase context
            if current_user and not self.created_by:
                self.created_by = current_user
        else:
            # Modification phase context
            self.updated_at = timezone.now()
            if current_user:
                self.updated_by = current_user
                
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        """ Performs a logical soft-delete instead of destroying raw rows. """
        self.deleted_at = timezone.now()
        if user:
            self.deleted_by = user
        self.save(update_fields=['deleted_at', 'deleted_by'])

    def restore(self):
        """ Un-deletes a previously soft-deleted instance. """
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['deleted_at', 'deleted_by'])