"""
users/models/role.py

Role model — RBAC ka pehla piece.

Roles define karte hain ki user kaun hai:
    - super_admin  → sab kuch access
    - author       → apne posts manage kare
    - reader       → sirf padhna

Role → Users (one-to-many): ek role ke kai users ho sakte hain
Role → RolePermission (one-to-many): ek role ke kai permissions
"""

from django.db import models
from core.models import BaseModel


class Role(BaseModel):
    """
    User roles table.

    code field kyun?
        name: "Super Admin"  ← display ke liye (change ho sakta hai)
        code: "super_admin"  ← logic ke liye (stable, kabhi change nahi)

    Permission check mein hum code use karenge:
        if user.role.code == "super_admin": ...
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Display name, e.g. 'Super Admin'",
    )
    code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Stable identifier, e.g. 'super_admin'. Logic mein isko use karo.",
    )
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(
        default=True,
        help_text="False = role inactive, us role ke users login nahi kar sakte",
    )

    class Meta:
        db_table = "roles"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code"],       name="idx_roles_code"),
            models.Index(fields=["status"],     name="idx_roles_status"),
            models.Index(fields=["deleted_at"], name="idx_roles_deleted_at"),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"