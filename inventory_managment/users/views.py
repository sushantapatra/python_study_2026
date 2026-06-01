# users/views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from users.serializers import UserRegisterSerializer, CustomTokenObtainPairSerializer

class UserRegistrationAPIView(APIView):
    """
    Handles secure user registration ingestion pipelines.
    """
    # Instructs drf-spectacular's introspection engine to parse this schema mapping
    serializer_class = UserRegisterSerializer

    @extend_schema(
        request=UserRegisterSerializer,
        responses={201: UserRegisterSerializer},
        summary="Register a new system user entity",
        description="Ingests user credentials, hashes security parameters, and initializes auditing transaction matrices."
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "User registered successfully",
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email
                    }
                }, 
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Handles custom claims generation for stateless JWT authorization maps.
    """
    serializer_class = CustomTokenObtainPairSerializer