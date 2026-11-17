"""
routers/relations.py — Les relations entre deux champs.

Rappel de la convention (voir models.py) :
  value_from = champ référencé, côté "un"           (ex. auteur.id)
  value_to   = champ qui référence, côté "plusieurs" (ex. livre.auteur_id)
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import models
import schemas
from access import get_owned_field, get_owned_relation, get_owned_schema
from database import get_db
from security import get_current_user

router = APIRouter(prefix="/relations", tags=["Relations"])


@router.post("/", response_model=schemas.RelationRead, status_code=201)
def create_relation(
    data: schemas.RelationCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    field_from = get_owned_field(db, data.value_from, user)
    field_to = get_owned_field(db, data.value_to, user)
    if field_from.parent_table.schema != field_to.parent_table.schema:
        raise HTTPException(status_code=400, detail="Les deux champs doivent appartenir au même schéma.")

    relation = models.Relation(**data.model_dump())
    db.add(relation)
    db.commit()
    db.refresh(relation)
    return relation


@router.get("/", response_model=list[schemas.RelationRead])
def list_relations(
    schema_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Relations de l'utilisateur ; ?schema_id=… pour celles d'un seul schéma."""
    query = (
        db.query(models.Relation)
        .join(models.Field, models.Relation.value_from == models.Field.id)
        .join(models.Table, models.Field.table == models.Table.id)
        .join(models.Schema, models.Table.schema == models.Schema.id)
        .filter(models.Schema.owner == user.id)
    )
    if schema_id is not None:
        query = query.filter(models.Schema.id == schema_id)
    return query.all()


@router.get("/{relation_id}", response_model=schemas.RelationRead)
def read_relation(relation_id: uuid.UUID, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return get_owned_relation(db, relation_id, user)


@router.put("/{relation_id}", response_model=schemas.RelationRead)
def change_relation_type(
    relation_id: uuid.UUID,
    data: schemas.RelationUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    relation = get_owned_relation(db, relation_id, user)
    relation.type = data.type
    db.commit()
    db.refresh(relation)
    return relation


@router.delete("/{relation_id}", status_code=204)
def delete_relation(relation_id: uuid.UUID, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db.delete(get_owned_relation(db, relation_id, user))
    db.commit()
