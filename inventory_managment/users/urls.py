from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import UserRegistrationAPIView, CustomTokenObtainPairView

app_name = 'users'

urlpatterns = [
    path('register/', UserRegistrationAPIView.as_view(), name='user_register'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]