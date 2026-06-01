from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role', 'phone_number']

    def create(self, validated_data):
        from users.services import UserService
        return UserService.create_user(validated_data)

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Generates basic tokens configuration matrices
        data = super().validate(attrs)
        
        # Inject custom response parameters dynamically
        data['username'] = self.user.username
        data['email'] = self.user.email
        data['role'] = getattr(self.user, 'role', 'OPERATOR')
        
        return data