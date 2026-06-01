from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from auditing.models import UserTransactionLogger
from users.models import UserRole

User = get_user_model()

class UserService:
    """
    SOLID Compliance: Single Responsibility.
    Manages identity management, role provisioning, and transaction audit trails.
    """
    @staticmethod
    @transaction.atomic
    def create_user(user_data, requested_by_ip="127.0.0.1"):
        """
        Validates business constraints, hashes passwords securely, 
        and updates the immutable audit ledger.
        """
        email = user_data.get('email')
        username = user_data.get('username')

        if User.objects.filter(username=username).exists():
            raise ValidationError({"username": "A user with this username already exists."})
        if User.objects.filter(email=email).exists():
            raise ValidationError({"email": "A user with this email identity already exists."})

        password = user_data.pop('password')
        role = user_data.get('role', UserRole.OPERATOR)

        user = User(
            username=username,
            email=email,
            role=role,
            phone_number=user_data.get('phone_number', ''),
            is_active=True
        )
        user.set_password(password)
        user.save()

        UserTransactionLogger.objects.create(
            user=user,
            module_name="USER_MANAGEMENT",
            action="CREATE",
            old_state=None,
            new_state={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            },
            ip_address=requested_by_ip
        )

        return user