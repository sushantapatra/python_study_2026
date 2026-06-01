# core/middleware.py
import contextvars
from django.http import HttpRequest, HttpResponse
from typing import Callable, Optional, Any

# REMOVED: User = get_user_model() to break the circular compilation lock

# Type hint using Any to prevent importing the model before the registry populates
_current_user_context = contextvars.ContextVar("current_user", default=None)

class GlobalUserRequestContextMiddleware:
    """
    SOLID Compliance: Single Responsibility.
    Captures the authenticated request user and binds it to a thread-safe context variable.
    """
    def __init__(self, get_response) -> None:
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        
        # Isolate anonymous users
        if user and not user.is_authenticated:
            user = None
            
        token = _current_user_context.set(user)
        try:
            response = self.get_response(request)
        finally:
            _current_user_context.reset(token)
            
        return response

def get_current_thread_user():
    """Retrieves the globally isolated current user executing the request payload."""
    return _current_user_context.get()