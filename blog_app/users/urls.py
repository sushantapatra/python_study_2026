"""
users/urls.py — All Users App Routes

Auth endpoints:
    POST   /api/v1/auth/register/
    POST   /api/v1/auth/login/
    POST   /api/v1/auth/logout/
    POST   /api/v1/auth/logout-all/
    POST   /api/v1/auth/token/refresh/
    GET    /api/v1/auth/profile/
    POST   /api/v1/auth/profile/update/
    POST   /api/v1/auth/change-password/
    POST   /api/v1/auth/forgot-password/
    POST   /api/v1/auth/reset-password/

RBAC endpoints:
    POST   /api/v1/roles/list/
    POST   /api/v1/roles/
    GET    /api/v1/roles/<id>/
    POST   /api/v1/roles/<id>/
    DELETE /api/v1/roles/<id>/
    (same pattern for menus, actions, permissions)
"""

from django.urls import path
from users.views import (
    # Auth
    RegisterView, LoginView, LogoutView, LogoutAllView,
    TokenRefreshView, ProfileView, ProfileUpdateView,
    ChangePasswordView, ForgotPasswordView, ResetPasswordView,
    # RBAC
    RoleListView, RoleCreateView, RoleDetailView,
    MenuListView, MenuCreateView, MenuDetailView,
    ActionListView, ActionCreateView, ActionDetailView,
    RolePermissionListView, RolePermissionCreateView, RolePermissionDetailView,
)

urlpatterns = [

    # ── Authentication ────────────────────────────────────────
    path("auth/register/",       RegisterView.as_view(),       name="auth-register"),
    path("auth/login/",          LoginView.as_view(),           name="auth-login"),
    path("auth/logout/",         LogoutView.as_view(),          name="auth-logout"),
    path("auth/logout-all/",     LogoutAllView.as_view(),       name="auth-logout-all"),
    path("auth/token/refresh/",  TokenRefreshView.as_view(),    name="auth-token-refresh"),
    path("auth/forgot-password/",ForgotPasswordView.as_view(),  name="auth-forgot-password"),
    path("auth/reset-password/", ResetPasswordView.as_view(),   name="auth-reset-password"),

    # ── Profile ───────────────────────────────────────────────
    path("auth/profile/",        ProfileView.as_view(),         name="auth-profile"),
    path("auth/profile/update/", ProfileUpdateView.as_view(),   name="auth-profile-update"),
    path("auth/change-password/",ChangePasswordView.as_view(),  name="auth-change-password"),

    # ── Roles ─────────────────────────────────────────────────
    path("roles/list/",          RoleListView.as_view(),        name="role-list"),
    path("roles/",               RoleCreateView.as_view(),      name="role-create"),
    path("roles/<int:pk>/",      RoleDetailView.as_view(),      name="role-detail"),

    # ── Menus ─────────────────────────────────────────────────
    path("menus/list/",          MenuListView.as_view(),        name="menu-list"),
    path("menus/",               MenuCreateView.as_view(),      name="menu-create"),
    path("menus/<int:pk>/",      MenuDetailView.as_view(),      name="menu-detail"),

    # ── Actions ───────────────────────────────────────────────
    path("actions/list/",        ActionListView.as_view(),      name="action-list"),
    path("actions/",             ActionCreateView.as_view(),    name="action-create"),
    path("actions/<int:pk>/",    ActionDetailView.as_view(),    name="action-detail"),

    # ── Role Permissions ──────────────────────────────────────
    path("permissions/list/",    RolePermissionListView.as_view(),    name="permission-list"),
    path("permissions/",         RolePermissionCreateView.as_view(),  name="permission-create"),
    path("permissions/<int:pk>/",RolePermissionDetailView.as_view(),  name="permission-detail"),
]