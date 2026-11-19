"""Tests de l'export SQL et du diagramme entité-relation."""
import sqlite3

import pytest


@pytest.fixture
def library_with_relation(client, alice, library):
    body = {"value_from": library["author.id"], "value_to": library["book.author_id"], "type": "OM"}
    assert client.post("/relations/", json=body, headers=alice).status_code == 201
    return library


def get_sql(client, headers, schema_id, dialect):
    response = client.get(f"/schemas/{schema_id}/sql", params={"dialect": dialect}, headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_postgresql_export(client, alice, library_with_relation):
    result = get_sql(client, alice, library_with_relation["schema"], "postgresql")
    sql = result["sql"]
    assert result["warnings"] == []
    assert 'CREATE TABLE "author"' in sql
    assert '"name" VARCHAR(100) NOT NULL' in sql
    assert 'PRIMARY KEY ("id")' in sql
    # la clé étrangère est sur book.author_id et pointe vers author.id
    assert 'ALTER TABLE "book" ADD CONSTRAINT "fk_book_author_id" FOREIGN KEY ("author_id") REFERENCES "author" ("id");' in sql


def test_mysql_uses_backticks(client, alice, library_with_relation):
    sql = get_sql(client, alice, library_with_relation["schema"], "mysql")["sql"]
    assert "CREATE TABLE `author`" in sql


def test_sqlite_script_really_runs(client, alice, library_with_relation):
    """Le meilleur test : on exécute le script dans une vraie base SQLite en mémoire."""
    sql = get_sql(client, alice, library_with_relation["schema"], "sqlite")["sql"]
    connection = sqlite3.connect(":memory:")
    connection.executescript(sql)
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert tables == {"author", "book"}


def test_many_to_many_creates_a_junction_table(client, alice, library):
    body = {"value_from": library["author.id"], "value_to": library["book.id"], "type": "MM"}
    client.post("/relations/", json=body, headers=alice)
    sql = get_sql(client, alice, library["schema"], "sqlite")["sql"]
    assert 'CREATE TABLE "author_book"' in sql
    sqlite3.connect(":memory:").executescript(sql)  # le script doit être valide


def test_warning_when_no_primary_key(client, alice, library):
    client.put(f"/fields/{library['author.id']}", json={"is_primary_key": False}, headers=alice)
    warnings = get_sql(client, alice, library["schema"], "postgresql")["warnings"]
    assert any("has no primary key" in w for w in warnings)


def test_er_diagram(client, alice, library_with_relation):
    response = client.get(f"/schemas/{library_with_relation['schema']}/dsd", headers=alice)
    assert response.status_code == 200
    text = response.text
    assert "erDiagram" in text
    assert "INT id PK" in text
    assert "INT author_id FK" in text
    assert "author ||--o{ book" in text


def test_export_file_download(client, alice, library):
    response = client.get(f"/schemas/{library['schema']}/export", params={"dialect": "sqlite"}, headers=alice)
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    assert "Library_sqlite.sql" in response.headers["content-disposition"]
