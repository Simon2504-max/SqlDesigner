"""Tests des comptes : inscription, connexion, jeton."""
from tests.conftest import register_and_login


def test_register_and_login(client):
    headers = register_and_login(client, "simon")
    me = client.get("/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["username"] == "simon"
    assert "password_hash" not in me.json()  # le mot de passe ne doit jamais sortir


def test_duplicate_username_is_refused(client):
    register_and_login(client, "simon")
    response = client.post(
        "/register", json={"username": "simon", "email": "other@example.com", "password": "password123"}
    )
    assert response.status_code == 409


def test_short_password_is_refused(client):
    response = client.post("/register", json={"username": "simon", "email": "s@example.com", "password": "123"})
    assert response.status_code == 422
    assert "password" in response.json()["detail"]


def test_wrong_password(client):
    register_and_login(client, "simon")
    response = client.post("/login", json={"username": "simon", "password": "wrong-password"})
    assert response.status_code == 401


def test_protected_route_needs_a_token(client):
    assert client.get("/me").status_code == 401
    assert client.get("/schemas/").status_code == 401


def test_fake_token_is_refused(client):
    response = client.get("/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
