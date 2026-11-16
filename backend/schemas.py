"""
schemas.py — Format et validation des données échangées avec l'interface.

Ces classes (Pydantic) décrivent ce que l'API accepte en entrée (…Create, …Update)
et ce qu'elle renvoie en sortie (…Read, …Out). Si une requête ne respecte pas
ces règles, FastAPI la refuse automatiquement avec une erreur 422 détaillée.

À ne pas confondre avec models.py, qui décrit les tables de la base de données.
"""
from typing import Annotated, Literal, Optional

from pydantic import (
    UUID4,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    model_validator,
)

from models import SQL_RELATION_TYPES, SQL_TYPES

# Ce que "from schemas import *" a le droit d'importer
__all__ = [
    "UUID4",
    "UserCreate", "UserUpdate", "UserOut", "UserLogin",
    "SchemaCreate", "SchemaRead",
    "TablesCreate", "TablesRead",
    "FieldCreate", "FieldRead",
    "RelationCreate", "RelationRead",
]

# ---------------------------------------------------------------------------
# Types réutilisables
# ---------------------------------------------------------------------------

# Nom SQL valide : commence par une lettre ou _, puis lettres, chiffres ou _.
# (pas d'espace, pas d'accent, pas de tiret : sinon le SQL généré serait invalide)
SqlIdentifier = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=63,
        pattern=r"^[A-Za-z_][A-Za-z0-9_]*$",
    ),
]

# Texte libre non vide (ex. nom d'un schéma)
NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class ORMModel(BaseModel):
    """Modèle de sortie qui peut être construit directement depuis un objet SQLAlchemy."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ---------------------------------------------------------------------------
# Utilisateurs
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    # Les règles sur la longueur du nom et du mot de passe seront ajoutées
    # à l'étape 9, en même temps que l'affichage des erreurs dans l'interface.
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class UserOut(ORMModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


# ---------------------------------------------------------------------------
# Schémas (projets)
# ---------------------------------------------------------------------------

class SchemaCreate(BaseModel):
    owner: int
    name: NonEmptyStr


class SchemaRead(ORMModel):
    id: UUID4
    owner: int
    name: str


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------

class TablesCreate(BaseModel):
    # En Python, l'attribut s'appelle schema_id (car "schema" est déjà un nom
    # utilisé par Pydantic) ; mais dans le JSON il s'appelle toujours "schema".
    model_config = ConfigDict(populate_by_name=True)

    schema_id: UUID4 = Field(alias="schema")
    name: SqlIdentifier


class TablesRead(ORMModel):
    id: UUID4
    schema_id: UUID4 = Field(alias="schema")
    name: str


# ---------------------------------------------------------------------------
# Champs
# ---------------------------------------------------------------------------

class FieldCreate(BaseModel):
    table: UUID4
    name: SqlIdentifier
    type: Literal[*SQL_TYPES]
    length: Optional[int] = Field(default=None, ge=1, le=65535)
    is_primary_key: bool = False
    is_nullable: bool = True
    is_unique: bool = False
    default_value: Optional[str] = None
    position: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def cle_primaire_jamais_vide(self):
        """Une clé primaire ne peut jamais être vide : on force NOT NULL."""
        if self.is_primary_key:
            self.is_nullable = False
        return self


class FieldRead(ORMModel):
    id: UUID4
    table: UUID4
    name: str
    type: str
    length: Optional[int] = None
    is_primary_key: bool = False
    is_nullable: bool = True
    is_unique: bool = False
    default_value: Optional[str] = None
    position: int = 0


# ---------------------------------------------------------------------------
# Relations
# ---------------------------------------------------------------------------

class RelationCreate(BaseModel):
    value_from: UUID4  # champ référencé, côté "un"       (ex. auteur.id)
    value_to: UUID4    # champ qui référence, côté "plusieurs" (ex. livre.auteur_id)
    type: Literal[*SQL_RELATION_TYPES]

    @model_validator(mode="after")
    def deux_champs_differents(self):
        if self.value_from == self.value_to:
            raise ValueError("Une relation doit relier deux champs différents.")
        return self


class RelationRead(ORMModel):
    id: UUID4
    value_from: UUID4
    value_to: UUID4
    type: str