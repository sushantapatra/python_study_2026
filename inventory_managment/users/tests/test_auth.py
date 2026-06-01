import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
@pytest.mark.unit
def test_user_registration_service_and_endpoint_flow(client):
    url = reverse('users:user_register')
    registration_payload = {
        "username": "inventory_admin",
        "email": "admin@inventory.com",
        "password": "SecurePassword123!",
        "role": "ADMIN",
        "phone_number": "1234567890"
    }
    response = client.post(url, data=registration_payload, content_type="application/json")
    assert response.status_code == 201

@pytest.mark.django_db
@pytest.mark.unit
def test_custom_jwt_claims_payload_login_assertion(client):
    user = User.objects.create_user(
        username="operator_dan",
        email="dan@inventory.com",
        password="DanPasswordAlpha123!",
        role="OPERATOR"
    )

    url = reverse('users:token_obtain_pair')
    login_credentials = {
        "username": "operator_dan",
        "password": "DanPasswordAlpha123!"
    }
    
    response = client.post(url, data=login_credentials, content_type="application/json")
    
    if response.status_code != 200:
        print("\n--- CRITICAL TEST LOG DATA ---")
        print(response.content)
        print("-------------------------------")
        
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data
    assert response.data["username"] == "operator_dan"
    assert response.data["email"] == "dan@inventory.com"
    assert response.data["role"] == "OPERATOR"