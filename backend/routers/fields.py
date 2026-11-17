"""
routers/fields.py — Les champs (colonnes) d'une table.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from access import get_owned_field, get_owned_schema, get_owned_table
from database import get_db
from security import get_current_user

router = APIRouter(prefix="/fields", tags=["Champs"])


@router.post("/", response_model=schemas.FieldRead, status_code=201)
def create_field(
    data: schemas.FieldCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    get_owned_table(db, data.table, user)
    values = data.model_dump()
    # Nouveau champ : placé à la fin de la table
    if not data.position:
        count = db.query(func.count(models.Field.id)).filter(models.Field.table == data.table).scalar()
        values["position"] = count
    field = models.Field(**values)
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.get("/table/{table_id}", response_model=list[schemas.FieldRead])
def list_fields_of_table(
    table_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return get_owned_table(db, table_id, user).fields


@router.get("/schema/{schema_id}", response_model=list[schemas.FieldRead])
def list_fields_of_schema(
    schema_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    schema = get_owned_schema(db, schema_id, user)
    return [field for table in schema.tables for field in table.fields]


@router.get("/{field_id}", response_model=schemas.FieldRead)
def read_field(field_id: uuid.UUID, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return get_owned_field(db, field_id, user)


@router.put("/{field_id}", response_model=schemas.FieldRead)
def update_field(
    field_id: uuid.UUID,
    data: schemas.FieldUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    field = get_owned_field(db, field_id, user)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(field, key, value)
    if field.is_primary_key:
        field.is_nullable = False
    db.commit()
    db.refresh(field)
    return field


@router.delete("/{field_id}", status_code=204)
def delete_field(field_id: uuid.UUID, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db.delete(get_owned_field(db, field_id, user))
    db.commit()
