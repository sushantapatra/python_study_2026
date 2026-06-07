"""
core/utils.py — Shared utility functions

Functions:
    get_client_ip()   → request se real IP address nikalo
    log_activity()    → ActivityLog entry create karo (one-liner helper)
"""

from django.utils import timezone


def get_client_ip(request):
    """
    Request se real IP address nikalo.

    Kyun X-Forwarded-For?
        Production mein app Nginx ya load balancer ke peeche hota hai.
        Direct request.META["REMOTE_ADDR"] sirf proxy ka IP deta hai.
        X-Forwarded-For header mein client ka actual IP hota hai.

    Format: "client_ip, proxy1_ip, proxy2_ip"
    Hum pehla (leftmost) IP lete hain — wahi original client hai.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "")
    return ip or None


def log_activity(
    request=None,
    user=None,
    model_name="",
    action_name="",
    object_id=None,
    before_input=None,
    after_input=None,
    description="",
):
    """
    ActivityLog entry create karo — ek simple helper.

    Usage:
        log_activity(
            request=request,
            model_name="Role",
            action_name="create",
            object_id=role.id,
            after_input={"name": role.name},
            description=f"Role '{role.name}' created.",
        )

    Note:
        - request ya user dono mein se ek dena zaroori hai
        - request se automatically ip_address aur user_agent nikalta hai
    """
    from users.models import ActivityLog  # Avoid circular import at module level

    # User determine karo
    actor = user
    if not actor and request and hasattr(request, "user") and request.user.is_authenticated:
        actor = request.user

    ip_address = get_client_ip(request) if request else None
    user_agent = request.META.get("HTTP_USER_AGENT", "") if request else ""

    ActivityLog.objects.create(
        user=actor,
        model_name=model_name,
        action_name=action_name,
        object_id=object_id,
        before_input=before_input,
        after_input=after_input,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )