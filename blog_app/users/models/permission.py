"""
users/models/permission.py

RolePermission model — Role + Menu + Action ka mapping.

Pehle wala approach (hardcoded booleans):
    can_add    = BooleanField
    can_edit   = BooleanField
    can_delete = BooleanField
    can_view   = BooleanField

    Problem: naya action chahiye? Model change karo, migration chalao.

Naya approach (dynamic via Action model):
    role   → FK to Role
    menu   → FK to Menu
    action → FK to Action

    Ek record = ek permission grant:
        (author_role, posts_menu, add_action)    ← author post add kar sakta hai
        (author_role, posts_menu, edit_action)   ← author post edit kar sakta hai
        (reader_role, posts_menu, view_action)   ← reader sirf dekh sakta hai

    Naya action? Sirf Action table mein add karo — model change nahi.

Permission check example:
    RolePermission.objects.filter(
        role=user.role,
        menu__code="posts_management",
        action__code="add",
        is_deleted=False,
    ).exists()
"""

from django.db import models
from core.models import BaseModel
from .role import Role
from .menu import Menu
from .action import Action


class RolePermission(BaseModel):
    """
    Role → Menu → Action ka granular permission mapping.

    unique_together (role, menu, action):
        Ek role ke paas ek menu ke liye ek action ka
        sirf ek record hoga — no duplicates.
    """

    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="permissions",
        db_column="role_id",
    )
    menu = models.ForeignKey(
        Menu,
        on_delete=models.CASCADE,
        related_name="permissions",
        db_column="menu_id",
    )
    action = models.ForeignKey(
        Action,
        on_delete=models.CASCADE,
        related_name="permissions",
        db_column="action_id",
    )

    class Meta:
        db_table = "role_permissions"
        unique_together = ("role", "menu", "action")
        indexes = [
            models.Index(fields=["role", "menu"],         name="idx_rp_role_menu"),
            models.Index(fields=["role", "menu", "action"], name="idx_rp_role_menu_action"),
            models.Index(fields=["is_deleted"],           name="idx_rp_is_deleted"),
        ]

    def __str__(self):
        return f"{self.role.code} → {self.menu.code} → {self.action.code}"