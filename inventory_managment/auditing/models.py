# auditing/models.py
from django.db import models
from django.conf import settings

class UserTransactionLogger(models.Model):
    """ Immutable ledger capturing human operations and delta adjustments. """
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOCK_ACQUIRED', 'Lock Acquired'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, db_index=True)
    module_name = models.CharField(max_length=100, db_index=True) # e.g., 'INVENTORY_STOCK'
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    
    # Store exact structural states to maintain system timelines
    old_state = models.JSONField(null=True, blank=True, help_text="State footprint before transformation.")
    new_state = models.JSONField(null=True, blank=True, help_text="State footprint after transformation.")
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_user_transactions'
        ordering = ['-timestamp']


class DataTransactionLogger(models.Model):
    """ Records ingress/egress contract communication structures with external boundaries. """
    STATUS_CHOICES = (
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        ('TIMEOUT', 'Timeout'),
    )

    endpoint_url = models.URLField(max_length=500)
    http_method = models.CharField(max_length=10)
    provider_name = models.CharField(max_length=100, db_index=True) # e.g., 'ERP_SYNC_VENDOR'
    
    request_payload = models.JSONField(null=True, blank=True)
    response_payload = models.JSONField(null=True, blank=True)
    status_code = models.PositiveIntegerField(null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    execution_time_ms = models.FloatField(help_text="Duration spent fulfilling the pipeline loop.")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_data_transactions'
        ordering = ['-timestamp']