"""
core/response.py

Standard API response helpers.

Kyun yeh helpers?
    Har view mein manually Response({...}) likhna repetitive hai
    aur galti hone ka chance hota hai. Yeh helpers ensure karte
    hain ki sab responses ek consistent format mein hain.

Usage:
    from core.response import success_response, error_response

    return success_response(data=serializer.data, message="Role created.")
    return error_response(message="Role not found.", status=404)
"""

from rest_framework.response import Response
from rest_framework import status as http_status


def success_response(data=None, message="Request successful.", status=http_status.HTTP_200_OK):
    """
    Create / Update / Delete ke liye success response.

    Format:
    {
        "status": "success",
        "message": "Role created successfully.",
        "data": { ... }
    }
    """
    payload = {
        "status":  "success",
        "message": message,
    }
    if data is not None:
        payload["data"] = data

    return Response(payload, status=status)


def error_response(message="An error occurred.", errors=None, status=http_status.HTTP_400_BAD_REQUEST):
    """
    Validation ya business logic errors ke liye.

    Format:
    {
        "status": "error",
        "message": "Validation failed.",
        "errors": { "name": ["This field is required."] }
    }
    """
    payload = {
        "status":  "error",
        "message": message,
    }
    if errors:
        payload["errors"] = errors

    return Response(payload, status=status)