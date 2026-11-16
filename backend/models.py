"""
models.py — Structure des tables de la base de données de l'application.

Chaque classe ci-dessous correspond à une table de la base :
  User      -> users      : les comptes utilisateurs
  Schema    -> schemas    : les schémas (projets de base de données) d'un utilisateur
  Table     -> tables     : les tables d'un schéma
  Field     -> fields     : les champs (colonnes) d'une table
  Relation  -> relations  : les liens entre deux champs

Convention pour les relations (utilisée par l'export SQL et les diagrammes) :
  value_from = le champ RÉFÉRENCÉ, côté "un"        (ex. auteur.id)
  value_to   = le champ qui RÉFÉRENCE, côté "plusieurs" (ex. livre.auteur_id)
  OO = un pour un, OM = un pour plusieurs, MM = plusieurs pour plusieurs
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

# Types SQL proposés pour les champs
SQL_TYPES = (
    "INT", "INTEGER", "SMALLINT", "BIGINT", "SERIAL",
    "DECIMAL", "NUMERIC", "FLOAT", "REAL", "DOUBLE",
    "CHAR", "VARCHAR", "TEXT",
    "DATE", "TIME", "TIMESTAMP", "DATETIME", "INTERVAL",
    "BOOLEAN",
    "BINARY", "VARBINARY", "BLOB",
    "UUID", "JSON", "JSONB", "ENUM", "ARRAY",
)

# Types de relations : un-un, un-plusieurs, plusieurs-plusieurs
SQL_RELATION_TYPES = ("OO", "OM", "MM")


class TimestampMixin:
    """Ajoute les dates de création et de modification à une table."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[Optional[str]] = mapped_column(String(100))
    phone: Mapped[Optional[str]] = mapped_column(String(20))

    schemas: Mapped[list["Schema"]] = relationship(
        back_populates="owner_user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Schema(TimestampMixin, Base):
    __tablename__ = "schemas"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))

    owner_user: Mapped["User"] = relationship(back_populates="schemas")
    tables: Mapped[list["Table"]] = relationship(
        back_populates="parent_schema",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Table.name",
    )


class Table(TimestampMixin, Base):
    __tablename__ = "tables"
    __table_args__ = (
        UniqueConstraint("schema", "name", name="uq_table_name_per_schema"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    schema: Mapped[uuid.UUID] = mapped_column(ForeignKey("schemas.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))

    parent_schema: Mapped["Schema"] = relationship(back_populates="tables")
    fields: Mapped[list["Field"]] = relationship(
        back_populates="parent_table",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by=lambda: [Field.position, Field.name],
    )


class Field(TimestampMixin, Base):
    __tablename__ = "fields"
    __table_args__ = (
        UniqueConstraint("table", "name", name="uq_field_name_per_table"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    table: Mapped[uuid.UUID] = mapped_column(ForeignKey("tables.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    type: Mapped[str] = mapped_column(Enum(*SQL_TYPES, name="sql_types"))

    # Nouvelles propriétés d'un champ
    length: Mapped[Optional[int]] = mapped_column(Integer)          # ex. VARCHAR(100)
    is_primary_key: Mapped[bool] = mapped_column(Boolean, default=False)
    is_nullable: Mapped[bool] = mapped_column(Boolean, default=True)  # False = NOT NULL
    is_unique: Mapped[bool] = mapped_column(Boolean, default=False)
    default_value: Mapped[Optional[str]] = mapped_column(String(255))
    position: Mapped[int] = mapped_column(Integer, default=0)       # ordre d'affichage

    parent_table: Mapped["Table"] = relationship(back_populates="fields")
    relations_from: Mapped[list["Relation"]] = relationship(
        foreign_keys="Relation.value_from",
        back_populates="field_from",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    relations_to: Mapped[list["Relation"]] = relationship(
        foreign_keys="Relation.value_to",
        back_populates="field_to",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Relation(TimestampMixin, Base):
    __tablename__ = "relations"
    __table_args__ = (
        UniqueConstraint("value_from", "value_to", name="uq_one_relation_per_pair"),
        CheckConstraint("value_from <> value_to", name="ck_no_self_relation"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    value_from: Mapped[uuid.UUID] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"))
    value_to: Mapped[uuid.UUID] = mapped_column(ForeignKey("fields.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(Enum(*SQL_RELATION_TYPES, name="sql_relation_types"))

    field_from: Mapped["Field"] = relationship(
        foreign_keys=[value_from], back_populates="relations_from"
    )
    field_to: Mapped["Field"] = relationship(
        foreign_keys=[value_to], back_populates="relations_to"
    )