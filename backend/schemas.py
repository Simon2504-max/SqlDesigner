"""
schemas.py — Format et validation des données échangées avec l'interface.

Ces classes (Pydantic) décrivent ce que l'API accepte en entrée (…Create, …Update)
et ce qu'elle renvoie en sortie (…Read, …Out). Si une requête ne respecte pas
ces règles, FastAPI la refuse automatiquement avec une erreur 422.

À ne pas confondre avec models.py, qui décrit les tables de la base de données.
"""
from typing import Annotated, Optional

from pydantic import (
    UUID4,
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    model_validator,
)

from models import SQL_RELATION_TYPES, SQL_TYPES

# ---------------------------------------------------------------------------
# Types et vérifications réutilisables
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


def check_sql_type(value: str) -> str:
    """Le type doit faire partie de SQL_TYPES (models.py)."""
    value = value.strip().upper()
    if value not in SQL_TYPES:
        raise ValueError(f"Type SQL inconnu : {value}")
    return value


def check_relation_type(value: str) -> str:
    """Le type de relation doit être OO, OM ou MM."""
    value = value.strip().upper()
    if value not in SQL_RELATION_TYPES:
        raise ValueError(f"Type de relation inconnu : {value} (OO, OM ou MM)")
    return value


# Types "texte + vérification" : la fonction s'exécute après la validation du texte
SqlType = Annotated[str, AfterValidator(check_sql_type)]
RelationType = Annotated[str, AfterValidator(check_relation_type)]


class ORMModel(BaseModel):
    """Modèle de sortie qui peut être construit directement depuis un objet SQLAlchemy."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ---------------------------------------------------------------------------
# Utilisateurs
# ---------------------------------------------------------------------------

class UserCreate(BaseModel):
    username: Annotated[str, StringConstraints(strip_whitespace=True, min_length=3, max_length=50)]
    email: EmailStr
    password: Annotated[str, StringConstraints(min_length=8, max_length=72)]
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


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------------------------------------------------------------------------
# Schémas (projets)
# ---------------------------------------------------------------------------

class SchemaCreate(BaseModel):
    # Le propriétaire n'est plus envoyé par l'interface : c'est l'utilisateur connecté.
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


class TableUpdate(BaseModel):
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
    type: SqlType
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


class FieldUpdate(BaseModel):
    """Modification d'un champ : on n'envoie que ce qui change."""

    name: Optional[SqlIdentifier] = None
    type: Optional[SqlType] = None
    length: Optional[int] = Field(default=None, ge=1, le=65535)
    is_primary_key: Optional[bool] = None
    is_nullable: Optional[bool] = None
    is_unique: Optional[bool] = None
    default_value: Optional[str] = None
    position: Optional[int] = Field(default=None, ge=0)


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
    value_from: UUID4  # champ référencé, côté "un"           (ex. auteur.id)
    value_to: UUID4    # champ qui référence, côté "plusieurs" (ex. livre.auteur_id)
    type: RelationType

    @model_validator(mode="after")
    def deux_champs_differents(self):
        if self.value_from == self.value_to:
            raise ValueError("Une relation doit relier deux champs différents.")
        return self


class RelationUpdate(BaseModel):
    type: RelationType


class RelationRead(ORMModel):
    id: UUID4
    value_from: UUID4
    value_to: UUID4
    type: str
