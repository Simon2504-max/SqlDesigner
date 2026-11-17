"""
routers/tables.py — Les tables d'un schéma.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import models
import schemas
from access import get_owned_schema, get_owned_table
from database import get_db
from security import get_current_user

router = APIRouter(prefix="/tables", tags=["Tables"])


@router.post("/", response_model=schemas.TablesRead, status_code=201)
def create_table(
    data: schemas.TablesCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    get_owned_schema(db, data.schema_id, user)
    table = models.Table(schema=data.schema_id, name=data.name)
    db.add(table)
    db.commit()
    db.refresh(table)
    return table


@router.get("/schema/{schema_id}", response_model=list[schemas.TablesRead])
def list_tables_of_schema(
    schema_id: uuid.UUID,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return get_owned_schema(db, schema_id, user).tables


@router.get("/{table_id}", response_model=schemas.TablesRead)
def read_table(table_id: uuid.UUID, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return get_owned_table(db, table_id, user)


@router.put("/{table_id}", response_model=schemas.TablesRead)
def rename_table(
    table_id: uuid.UUID,
    data: schemas.TableUpdate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    table = get_owned_table(db, table_id, user)
    table.name = data.name
    db.commit()
    db.refresh(table)
    return table


@router.delete("/{table_id}", status_code=204)
def delete_table(table_id: uuid.UUID, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db.delete(get_owned_table(db, table_id, user))
    db.commit()
