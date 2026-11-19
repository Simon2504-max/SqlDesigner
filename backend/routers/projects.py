"""
routers/projects.py — Les schémas (projets de base de données) de l'utilisateur.

Le fichier s'appelle "projects" et non "schemas" pour ne pas être confondu
avec schemas.py (les modèles Pydantic).
"""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy.orm import Session

import models
import schemas
from access import get_owned_schema
from database import get_db
from security import get_current_user
from diagram import generate_er_diagram
from sql_export import generate_sql

router = APIRouter(prefix="/schemas", tags=["Schémas"])

Dialect = Literal["postgresql", "mysql", "sqlite"]


@router.post("/", response_model=schemas.SchemaRead, status_code=201)
def create_schema(
    data: schemas.SchemaCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    # Le propriétaire est TOUJOURS l'utilisateur connecté (jamais une valeur envoyée par l'interface)
    schema = models.Schema(owner=user.id, name=data.name)
    db.add(schema)
    db.commit()
    db.refresh(schema)
    return schema


@router.get("/", response_model=list[schemas.SchemaRead])
def list_my_schemas(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return db.query(models.Schema).filter(models.Schema.owner == user.id).order_by(models.Schema.name).all()


@router.get("/owner/{owner_id}", response_model=list[schemas.SchemaRead], include_in_schema=False)
def list_my_schemas_legacy(owner_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Ancienne adresse, gardée pour l'interface actuelle : renvoie toujours MES schémas."""
    return list_my_schemas(db, user)


@router.get("/{schema_id}", response_model=schemas.SchemaRead)
def read_schema(schema_id: uuid.UUID, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return get_owned_schema(db, schema_id, user)


@router.put("/{schema_id}", response_model=schemas.SchemaRead)
def rename_schema(
    schema_id: uuid.UUID,
    data: schemas.SchemaCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    schema = get_owned_schema(db, schema_id, user)
    schema.name = data.name
    db.commit()
    db.refresh(schema)
    return schema


@router.delete("/{schema_id}", status_code=204)
def delete_schema(schema_id: uuid.UUID, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    db.delete(get_owned_schema(db, schema_id, user))
    db.commit()


# ---------------------------------------------------------------------------
# Diagramme entité-relation (étape 8) : voir diagram.py
# ---------------------------------------------------------------------------

@router.get("/{schema_id}/dsd", response_class=PlainTextResponse)
def get_dsd_diagram(schema_id: uuid.UUID, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Le texte Mermaid (erDiagram) du schéma, que l'interface transforme en image."""
    return generate_er_diagram(get_owned_schema(db, schema_id, user))


# ---------------------------------------------------------------------------
# Export SQL (étape 7) : voir sql_export.py
# ---------------------------------------------------------------------------

@router.get("/{schema_id}/sql", response_model=schemas.SqlExport)
def preview_sql(
    schema_id: uuid.UUID,
    dialect: Dialect = "postgresql",
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Le script SQL en JSON (pour l'afficher dans l'interface), avec les avertissements."""
    result = generate_sql(get_owned_schema(db, schema_id, user), dialect)
    return {"dialect": dialect, "sql": result.sql, "warnings": result.warnings}


@router.get("/{schema_id}/export")
def export_schema(
    schema_id: uuid.UUID,
    dialect: Dialect = "postgresql",
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Le script SQL sous forme de fichier .sql à télécharger."""
    schema = get_owned_schema(db, schema_id, user)
    result = generate_sql(schema, dialect)
    filename = f"{schema.name}_{dialect}.sql".replace(" ", "_")
    return Response(
        content=result.sql,
        media_type="application/sql",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
