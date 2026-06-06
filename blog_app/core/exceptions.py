"""
core/exceptions.py

Custom exception handler — sab API errors ek consistent format mein aate hain.

Default DRF format:    {"detail": "Not found."}
Hamara format:         {"status": "error", "message": "...", "errors": {...}}
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    DRF ka default exception handler pehle call karo.
    Phir response ko apne consistent format mein wrap karte hain.
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_data = response.data

        if isinstance(error_data, dict):
            if "detail" in error_data:
                message = str(error_data["detail"])
                errors = None
            else:
                # Field-level validation errors
                message = "Validation failed. Please check the errors below."
                errors = error_data
        elif isinstance(error_data, list):
            message = error_data[0] if error_data else "An error occurred."
            errors = None
        else:
            message = str(error_data)
            errors = None

        custom_response = {
            "status": "error",
            "message": message,
        }
        if errors:
            custom_response["errors"] = errors

        response.data = custom_response

    else:
        # Unexpected server error (500)
        logger.exception("Unhandled exception: %s", exc)
        response = Response(
            {
                "status": "error",
                "message": "An unexpected server error occurred. Please try again.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response