"""
users/models/menu.py

Menu / Module model — RBAC ka doosra piece.

"Menu" matlab ek feature module/section:
    - Users Management
    - Posts Management
    - Categories Management
    - Comments Management
    - Analytics
    - Settings
    ...

Har menu ko ek Role ke saath actions assign kiye jaate hain
(RolePermission table mein).

parent field kyun?
    Sub-menus support karne ke liye:
    Posts Management (parent)
    └── Published Posts  (child)
    └── Draft Posts      (child)
    └── Archived Posts   (child)
"""

from django.db import models
from core.models import BaseModel


class Menu(BaseModel):
    """
    Application menus / modules.

    name:  "Posts Management"
    code:  "posts_management"   ← permission check mein use hoga
    icon:  "file-text"          ← React frontend sidebar icon ke liye
    order: 1, 2, 3...           ← sidebar display order
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Display name, e.g. 'Posts Management'",
    )
    code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Stable identifier, e.g. 'posts_management'",
    )
    icon = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Icon name for React frontend sidebar",
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Sidebar display order (0 = first)",
    )
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        db_column="parent_id",
        help_text="Sub-menu ka parent menu",
    )
    status = models.BooleanField(default=True)

    class Meta:
        db_table = "menus"
        ordering = ["order", "name"]
        indexes = [
            models.Index(fields=["code"],       name="idx_menus_code"),
            models.Index(fields=["parent"],     name="idx_menus_parent"),
            models.Index(fields=["status"],     name="idx_menus_status"),
            models.Index(fields=["deleted_at"], name="idx_menus_deleted_at"),
        ]

    def __str__(self):
        return self.name