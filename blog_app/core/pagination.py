"""
core/pagination.py

Standard pagination — sab List APIs mein yahi use hogi.

Response format:
{
    "success": true,
    "message": "Request successful.",
    "data": {
        "count": 100,
        "next": "http://localhost:8000/api/v1/roles/?page=3",
        "previous": "http://localhost:8000/api/v1/roles/?page=1",
        "results": [...]
    }
}

page_size = 10       → default 10 records per page
page_size_query_param → client ?page_size=25 se change kar sakta hai
max_page_size = 100  → client 100 se zyada nahi maang sakta
"""

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    page_size              = 10
    page_size_query_param  = "page_size"
    max_page_size          = 100
    page_query_param       = "page"

    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "message": "Request successful.",
            "data": {
                "count":    self.page.paginator.count,
                "next":     self.get_next_link(),
                "previous": self.get_previous_link(),
                "results":  data,
            }
        })

    def get_paginated_response_schema(self, schema):
        """
        drf-spectacular ke liye — Swagger docs mein
        paginated response ka sahi schema dikhega.
        """
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "example": True},
                "message": {"type": "string",  "example": "Request successful."},
                "data": {
                    "type": "object",
                    "properties": {
                        "count":    {"type": "integer", "example": 100},
                        "next":     {"type": "string",  "nullable": True},
                        "previous": {"type": "string",  "nullable": True},
                        "results":  schema,
                    }
                }
            }
        }