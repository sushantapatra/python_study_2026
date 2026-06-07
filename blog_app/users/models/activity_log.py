"""
users/models/activity_log.py

ActivityLog — har user action ka record.

Note: BaseModel se inherit NAHI karta.
    Logs kabhi delete nahi hote — soft delete ki zarurat nahi.
    Aur log ke liye created_by/updated_by audit trail nahi chahiye.

Usage:
    ActivityLog.objects.create(
        user=request.user,
        model_name="Role",
        action_name="create",
        object_id=role.id,
        after_input={"name": "Admin"},
        description="Role created.",
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )
"""

from django.db import models


class ActivityLog(models.Model):
    user = models.ForeignKey(
        "users.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="activity_logs",
        db_column="user_id",
    )
    model_name   = models.CharField(max_length=100, db_index=True)
    action_name  = models.CharField(max_length=100, db_index=True)
    object_id    = models.BigIntegerField(null=True, blank=True, db_index=True)
    before_input = models.JSONField(null=True, blank=True)
    after_input  = models.JSONField(null=True, blank=True)
    description  = models.TextField(null=True, blank=True)
    ip_address   = models.GenericIPAddressField(null=True, blank=True)
    user_agent   = models.TextField(null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "activity_logs"
        ordering = ["-created_at"]
        indexes  = [
            models.Index(fields=["user", "created_at"],        name="idx_al_user_created"),
            models.Index(fields=["model_name", "action_name"], name="idx_al_model_action"),
        ]

    def __str__(self):
        user_str = self.user.email if self.user else "anonymous"
        return f"[{self.action_name}] {self.model_name} by {user_str}"