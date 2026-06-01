from django.contrib.auth.models import AbstractUser
from django.db import models
from core.models import BaseModel

class UserRole(models.TextChoices):
    ADMIN = 'ADMIN', 'System Administrator'
    WAREHOUSE_MANAGER = 'WAREHOUSE_MANAGER', 'Warehouse Manager'
    OPERATOR = 'OPERATOR', 'Inventory Operator'

class CustomUser(AbstractUser, BaseModel):
    """
    Enterprise Identity Access Management Core Model.
    Binds standard login features with centralized audit vectors and RBAC.
    """
    role = models.CharField(
        max_length=30,
        choices=UserRole.choices,
        default=UserRole.OPERATOR,
        db_index=True,
        help_text="Security context indicator driving endpoint routing accessibility matrix."
    )
    # Overriding email to enforce a safe index allocation boundary for utf8mb4
    email = models.EmailField(unique=True, max_length=190)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'users_custom_user'
        ordering = ['-id']

    def __str__(self) -> str:
        return f"{self.username} -> {self.role}"