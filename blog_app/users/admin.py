"""
users/admin.py

Django Admin mein User model register karo.
Isse /admin/ panel pe users manage kar sakte hain.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from users.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom UserAdmin — email-based auth ke liye adjust kiya.
    BaseUserAdmin se inherit karne se password change form
    aur permission management automatically milta hai.
    """

    list_display  = ("email", "first_name", "last_name", "is_active", "is_staff", "created_at")
    list_filter   = ("is_active", "is_staff", "is_email_verified")
    search_fields = ("email", "first_name", "last_name")
    ordering      = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "last_login")

    fieldsets = (
        ("Login Info",   {"fields": ("email", "password")}),
        ("Personal",     {"fields": ("first_name", "last_name", "phone", "bio", "avatar_url")}),
        ("Role",         {"fields": ("role",)}),
        ("Permissions",  {"fields": ("is_active", "is_staff", "is_superuser",
                                      "is_email_verified", "groups", "user_permissions")}),
        ("Audit",        {"fields": ("created_at", "updated_at", "last_login")}),
        ("Soft Delete",  {"fields": ("deleted_at", "deleted_by")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2"),
        }),
    )

    # BaseUserAdmin username fields ko override karo
    filter_horizontal = ("groups", "user_permissions")