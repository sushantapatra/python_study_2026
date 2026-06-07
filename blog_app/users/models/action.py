"""
users/models/action.py

Action model — RBAC ka teesra piece.

Kyun alag Action model chahiye?
    Agar actions hardcode karein (can_add, can_edit, can_delete, can_view)
    to future mein naya action add karna = model change + migration.

    Action model se yeh dynamic ho jaata hai:
        - "add", "edit", "delete", "view"  ← default actions
        - "export", "approve", "publish"   ← future mein easily add karo
        - Koi bhi custom action bina model change ke

Standard default actions:
    code: "add"    → POST   (record create karna)
    code: "edit"   → PUT/PATCH (record update karna)
    code: "delete" → DELETE (soft delete karna)
    code: "view"   → GET    (list + detail dekhna)
"""

from django.db import models
from core.models import BaseModel


class Action(BaseModel):
    """
    Granular actions jo ek Role ko ek Menu pe karne ki
    permission di ja sakti hai.

    name: "Add"     ← display ke liye
    code: "add"     ← permission check mein use hoga
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Display name, e.g. 'Add', 'Export'",
    )
    code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Stable identifier used in permission checks, e.g. 'add', 'export'",
    )
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "actions"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code"],       name="idx_actions_code"),
            models.Index(fields=["status"],     name="idx_actions_status"),
            models.Index(fields=["deleted_at"], name="idx_actions_deleted_at"),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"