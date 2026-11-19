"""
access.py — Vérifie qu'un objet existe ET appartient à l'utilisateur connecté.

Chaque fonction renvoie l'objet demandé, ou lève une erreur 404.
On répond volontairement 404 (et non 403) quand l'objet appartient à quelqu'un
d'autre : ainsi, on ne révèle même pas qu'il existe.
"""
import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

import models


def get_owned_schema(db: Session, schema_id: uuid.UUID, user: models.User) -> models.Schema:
    schema = db.get(models.Schema, schema_id)
    if schema is None or schema.owner != user.id:
        raise HTTPException(status_code=404, detail="Schema not found.")
    return schema


def get_owned_table(db: Session, table_id: uuid.UUID, user: models.User) -> models.Table:
    table = db.get(models.Table, table_id)
    if table is None or table.parent_schema.owner != user.id:
        raise HTTPException(status_code=404, detail="Table not found.")
    return table


def get_owned_field(db: Session, field_id: uuid.UUID, user: models.User) -> models.Field:
    field = db.get(models.Field, field_id)
    if field is None or field.parent_table.parent_schema.owner != user.id:
        raise HTTPException(status_code=404, detail="Field not found.")
    return field


def get_owned_relation(db: Session, relation_id: uuid.UUID, user: models.User) -> models.Relation:
    relation = db.get(models.Relation, relation_id)
    if relation is None or relation.field_from.parent_table.parent_schema.owner != user.id:
        raise HTTPException(status_code=404, detail="Relation not found.")
    return relation
