"""Tests de l'éditeur : schémas, tables, champs, relations, et isolation entre utilisateurs."""


def test_create_and_list_schemas(client, alice):
    client.post("/schemas/", json={"name": "Shop"}, headers=alice)
    client.post("/schemas/", json={"name": "Blog"}, headers=alice)
    names = [s["name"] for s in client.get("/schemas/", headers=alice).json()]
    assert names == ["Blog", "Shop"]  # triés par nom


def test_users_cannot_see_each_other(client, alice, bob, library):
    # bob ne voit pas le schéma d'alice…
    assert client.get("/schemas/", headers=bob).json() == []
    # …et ne peut ni le lire, ni le supprimer, ni y ajouter une table
    assert client.get(f"/schemas/{library['schema']}", headers=bob).status_code == 404
    assert client.delete(f"/schemas/{library['schema']}", headers=bob).status_code == 404
    response = client.post("/tables/", json={"schema": library["schema"], "name": "hack"}, headers=bob)
    assert response.status_code == 404


def test_invalid_table_name_is_refused(client, alice, library):
    response = client.post("/tables/", json={"schema": library["schema"], "name": "my table"}, headers=alice)
    assert response.status_code == 422


def test_duplicate_field_gives_409(client, alice, library):
    body = {"table": library["book"], "name": "title", "type": "TEXT"}
    response = client.post("/fields/", json=body, headers=alice)
    assert response.status_code == 409
    assert "duplicate" in response.json()["detail"]


def test_primary_key_is_always_not_null(client, alice, library):
    field = client.get(f"/fields/{library['author.id']}", headers=alice).json()
    assert field["is_primary_key"] is True
    assert field["is_nullable"] is False


def test_update_field(client, alice, library):
    response = client.put(
        f"/fields/{library['book.title']}", json={"type": "varchar", "length": 200, "is_unique": True}, headers=alice
    )
    assert response.status_code == 200
    field = response.json()
    assert field["type"] == "VARCHAR"  # mis en majuscules par la validation
    assert field["length"] == 200
    assert field["is_unique"] is True


def test_relation_lifecycle(client, alice, library):
    body = {"value_from": library["author.id"], "value_to": library["book.author_id"], "type": "OM"}
    created = client.post("/relations/", json=body, headers=alice)
    assert created.status_code == 201

    listed = client.get("/relations/", params={"schema_id": library["schema"]}, headers=alice).json()
    assert len(listed) == 1

    assert client.delete(f"/relations/{created.json()['id']}", headers=alice).status_code == 204
    assert client.get("/relations/", headers=alice).json() == []


def test_relation_to_itself_is_refused(client, alice, library):
    body = {"value_from": library["author.id"], "value_to": library["author.id"], "type": "OM"}
    assert client.post("/relations/", json=body, headers=alice).status_code == 422


def test_deleting_a_table_deletes_its_fields_and_relations(client, alice, library):
    body = {"value_from": library["author.id"], "value_to": library["book.author_id"], "type": "OM"}
    client.post("/relations/", json=body, headers=alice)

    assert client.delete(f"/tables/{library['book']}", headers=alice).status_code == 204

    fields = client.get(f"/fields/schema/{library['schema']}", headers=alice).json()
    assert {f["name"] for f in fields} == {"id", "name"}  # il ne reste que les champs d'author
    assert client.get("/relations/", headers=alice).json() == []  # suppression en cascade
