"""
conftest.py — Préparation commune à tous les tests (pytest le lit automatiquement).

- Les tests utilisent une base SQLite TEMPORAIRE, jamais ta vraie base.
- Avant chaque test, toutes les tables sont vidées puis recréées.
- Des "fixtures" (fonctions préparatoires) fournissent un client HTTP de test
  et des utilisateurs déjà connectés.
"""
import os
import tempfile

# IMPORTANT : on choisit la base AVANT d'importer l'application,
# car database.py lit DATABASE_URL au moment de son import.
_db_file = os.path.join(tempfile.gettempdir(), "sqldesigner_tests.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file}"
os.environ["SECRET_KEY"] = "test-secret-key"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import models  # noqa: E402
from database import engine  # noqa: E402
from main import app  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_database():
    """Avant CHAQUE test : base vide. (autouse = appliqué automatiquement)"""
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    """Un faux navigateur qui envoie des requêtes à l'application, sans lancer de serveur."""
    with TestClient(app) as test_client:
        yield test_client


def register_and_login(client, username):
    """Crée un compte, se connecte, et renvoie les en-têtes avec le jeton."""
    password = "password123"
    response = client.post(
        "/register", json={"username": username, "email": f"{username}@example.com", "password": password}
    )
    assert response.status_code == 201, response.text
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def alice(client):
    """En-têtes d'une utilisatrice connectée, « alice »."""
    return register_and_login(client, "alice")


@pytest.fixture
def bob(client):
    """En-têtes d'un deuxième utilisateur, « bob » (pour tester l'isolation)."""
    return register_and_login(client, "bob")


@pytest.fixture
def library(client, alice):
    """Un petit schéma prêt à l'emploi : author(id PK, name) et book(id PK, title, author_id)."""
    schema = client.post("/schemas/", json={"name": "Library"}, headers=alice).json()

    def table(name):
        return client.post("/tables/", json={"schema": schema["id"], "name": name}, headers=alice).json()

    def field(table_id, name, type_, **extra):
        body = {"table": table_id, "name": name, "type": type_, **extra}
        response = client.post("/fields/", json=body, headers=alice)
        assert response.status_code == 201, response.text
        return response.json()

    author = table("author")
    book = table("book")
    ids = {
        "schema": schema["id"],
        "author": author["id"],
        "book": book["id"],
        "author.id": field(author["id"], "id", "INT", is_primary_key=True)["id"],
        "author.name": field(author["id"], "name", "VARCHAR", length=100, is_nullable=False)["id"],
        "book.id": field(book["id"], "id", "INT", is_primary_key=True)["id"],
        "book.title": field(book["id"], "title", "VARCHAR")["id"],
        "book.author_id": field(book["id"], "author_id", "INT", is_nullable=False)["id"],
    }
    return ids
