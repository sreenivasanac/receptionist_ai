"""Tests for authentication endpoints."""
import pytest


def test_signup_business_owner(client):
    """Test business owner signup."""
    response = client.post("/auth/signup", json={
        "username": "testuser",
        "email": "test@example.com",
        "role": "business_owner",
        "business_name": "Test Salon",
        "business_type": "beauty"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["business_id"] is not None


def test_login(client):
    """Test login."""
    client.post("/auth/signup", json={
        "username": "logintest",
        "role": "business_owner",
        "business_name": "Login Test Salon",
        "business_type": "beauty"
    })
    
    response = client.post("/auth/login", json={
        "username": "logintest",
        "role": "business_owner"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "logintest"
    assert data["business"] is not None
