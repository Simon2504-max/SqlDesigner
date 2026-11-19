"""
sql_export.py — Transforme un schéma dessiné dans l'application en script SQL.

Trois "dialectes" (variantes du langage SQL) sont gérés :
  - postgresql : PostgreSQL
  - mysql      : MySQL / MariaDB
  - sqlite     : SQLite

Le script produit contient, dans l'ordre :
  1. un en-tête (commentaires) et les éventuels avertissements ;
  2. un CREATE TABLE par table (colonnes, NOT NULL, UNIQUE, DEFAULT, PRIMARY KEY) ;
  3. une table de liaison par relation N:N ;
  4. les clés étrangères (FOREIGN KEY).

Rappel de la convention des relations (voir models.py) :
  value_from = champ RÉFÉRENCÉ, côté "un"           (ex. auteur.id)
  value_to   = champ qui RÉFÉRENCE, côté "plusieurs" (ex. livre.auteur_id)
  => la clé étrangère est posée sur le champ value_to et pointe vers value_from.
"""
from dataclasses import dataclass, field as dc_field
from datetime import datetime, timezone

DIALECTS = ("postgresql", "mysql", "sqlite")

# Types de l'application -> type SQL de chaque dialecte (absent = inchangé)
TYPE_MAP = {
    "postgresql": {
        "INT": "INTEGER", "DOUBLE": "DOUBLE PRECISION", "DATETIME": "TIMESTAMP",
        "BLOB": "BYTEA", "BINARY": "BYTEA", "VARBINARY": "BYTEA",
        "ENUM": "TEXT", "ARRAY": "TEXT[]",
    },
    "mysql": {
        "INT": "INT", "UUID": "CHAR(36)", "JSONB": "JSON", "INTERVAL": "VARCHAR(64)",
        "ENUM": "VARCHAR(255)", "ARRAY": "JSON", "SERIAL": "INT AUTO_INCREMENT",
    },
    "sqlite": {
        "INT": "INTEGER", "SERIAL": "INTEGER", "UUID": "TEXT", "JSON": "TEXT", "JSONB": "TEXT",
        "ENUM": "TEXT", "ARRAY": "TEXT", "INTERVAL": "TEXT",
    },
}

# Types qui acceptent une longueur entre parenthèses, et leur longueur par défaut
LENGTH_TYPES = {"VARCHAR": 255, "CHAR": 1, "VARBINARY": 255, "BINARY": 1, "DECIMAL": None, "NUMERIC": None}

# Valeurs par défaut écrites telles quelles (pas entre guillemets)
SQL_KEYWORDS = {"NULL", "TRUE", "FALSE", "CURRENT_TIMESTAMP", "CURRENT_DATE", "CURRENT_TIME", "NOW()"}

@dataclass
class ExportResult:
    sql: str
    warnings: list[str] = dc_field(default_factory=list)


# ---------------------------------------------------------------------------
# Petits outils
# ---------------------------------------------------------------------------

def quote(name: str, dialect: str) -> str:
    """Entoure un nom de guillemets SQL (évite les conflits avec les mots réservés)."""
    if dialect == "mysql":
        return f"`{name}`"
    return f'"{name}"'


def column_type(field, dialect: str) -> str:
    """Type SQL complet d'un champ, ex. VARCHAR(100), INTEGER, TIMESTAMP."""
    base = field.type.upper()
    mapped = TYPE_MAP[dialect].get(base, base)
    if base in LENGTH_TYPES and "(" not in mapped:
        length = field.length or LENGTH_TYPES[base]
        if length:
            mapped = f"{mapped}({length})"
    return mapped


def default_clause(value: str) -> str:
    """Écrit DEFAULT … en mettant le texte entre apostrophes si nécessaire."""
    text = value.strip()
    if text.upper() in SQL_KEYWORDS:
        return f"DEFAULT {text.upper()}"
    try:
        float(text)
        return f"DEFAULT {text}"
    except ValueError:
        escaped = text.replace("'", "''")
        return f"DEFAULT '{escaped}'"


def base_type(field) -> str:
    """Type 'logique' pour comparer deux champs (SERIAL et INT = INTEGER…)."""
    t = field.type.upper()
    return {"SERIAL": "INTEGER", "INT": "INTEGER"}.get(t, t)


def reference_type(field, dialect: str) -> str:
    """Type à utiliser pour une colonne qui pointe vers ce champ."""
    t = field.type.upper()
    if t == "SERIAL":
        return "INT" if dialect == "mysql" else "INTEGER"
    return column_type(field, dialect)


def constraint_name(*parts: str) -> str:
    """Nom de contrainte lisible et limité à 63 caractères (limite PostgreSQL)."""
    return "_".join(parts)[:63]


# ---------------------------------------------------------------------------
# Génération
# ---------------------------------------------------------------------------

def generate_sql(schema, dialect: str = "postgresql") -> ExportResult:
    """Point d'entrée : produit le script SQL d'un schéma (objet models.Schema)."""
    if dialect not in DIALECTS:
        raise ValueError(f"Unknown dialect: {dialect}")

    q = lambda name: quote(name, dialect)  # noqa: E731
    warnings: list[str] = []

    tables = list(schema.tables)
    fields_by_id = {f.id: f for t in tables for f in t.fields}
    table_of = {f.id: t for t in tables for f in t.fields}

    # Relations dont les deux champs sont dans ce schéma (chacune une seule fois)
    relations = []
    seen = set()
    for f in fields_by_id.values():
        for r in f.relations_from:
            if r.value_to in fields_by_id and r.id not in seen:
                seen.add(r.id)
                relations.append(r)

    one_to_x = [r for r in relations if r.type in ("OO", "OM")]
    many_to_many = [r for r in relations if r.type == "MM"]

    # Pour une relation 1:1, la clé étrangère doit être UNIQUE
    needs_unique = {r.value_to for r in one_to_x if r.type == "OO"}

    # ---- Vérifications : on prévient l'utilisateur des problèmes probables ----
    for t in tables:
        if not t.fields:
            warnings.append(f"Table \"{t.name}\" has no field.")
        elif not any(f.is_primary_key for f in t.fields):
            warnings.append(f"Table \"{t.name}\" has no primary key.")

    for r in relations:
        parent, child = fields_by_id[r.value_from], fields_by_id[r.value_to]
        p_table, c_table = table_of[parent.id].name, table_of[child.id].name
        if not (parent.is_primary_key or parent.is_unique):
            warnings.append(
                f"{p_table}.{parent.name} is referenced by {c_table}.{child.name} "
                f"but is neither a primary key nor UNIQUE: the database will reject the foreign key."
            )
        if r.type != "MM" and base_type(parent) != base_type(child):
            warnings.append(
                f"Type mismatch: {c_table}.{child.name} ({child.type}) "
                f"references {p_table}.{parent.name} ({parent.type})."
            )

    # ---- En-tête ----
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    out: list[str] = [
        f"-- Schema: {schema.name}",
        f"-- Generated by SqlDesigner on {now}",
        f"-- Dialect: {dialect}",
    ]
    if warnings:
        out.append("--")
        out.append("-- ⚠ Warnings:")
        out.extend(f"--   - {w}" for w in warnings)
    out.append("")

    if dialect == "sqlite":
        out += ["PRAGMA foreign_keys = ON;", ""]
    if dialect == "postgresql":
        out += ["BEGIN;", ""]

    # Avec SQLite, impossible d'ajouter une clé étrangère après coup (pas de
    # ALTER TABLE … ADD CONSTRAINT) : on les écrit donc dans le CREATE TABLE.
    inline_fks = dialect == "sqlite"
    fks_by_table: dict = {}
    for r in one_to_x:
        fks_by_table.setdefault(table_of[r.value_to].id, []).append(r)

    # ---- 1. Les tables ----
    for t in tables:
        if not t.fields:
            continue
        lines = []
        pk_fields = [f for f in t.fields if f.is_primary_key]
        for f in t.fields:
            parts = [q(f.name), column_type(f, dialect)]
            if not f.is_nullable or f.is_primary_key:
                parts.append("NOT NULL")
            if (f.is_unique or f.id in needs_unique) and not (f.is_primary_key and len(pk_fields) == 1):
                parts.append("UNIQUE")
            if f.default_value:
                parts.append(default_clause(f.default_value))
            lines.append("    " + " ".join(parts))

        if pk_fields:
            cols = ", ".join(q(f.name) for f in pk_fields)
            lines.append(f"    CONSTRAINT {q(constraint_name('pk', t.name))} PRIMARY KEY ({cols})")

        if inline_fks:
            for r in fks_by_table.get(t.id, []):
                parent, child = fields_by_id[r.value_from], fields_by_id[r.value_to]
                lines.append(
                    f"    CONSTRAINT {q(constraint_name('fk', t.name, child.name))} "
                    f"FOREIGN KEY ({q(child.name)}) "
                    f"REFERENCES {q(table_of[parent.id].name)} ({q(parent.name)})"
                )

        out.append(f"CREATE TABLE {q(t.name)} (")
        out.append(",\n".join(lines))
        out.append(");")
        out.append("")

    # ---- 2. Les tables de liaison (relations N:N) ----
    existing_names = {t.name.lower() for t in tables}
    for r in many_to_many:
        left, right = fields_by_id[r.value_from], fields_by_id[r.value_to]
        lt, rt = table_of[left.id], table_of[right.id]
        name = f"{lt.name}_{rt.name}"
        while name.lower() in existing_names:
            name += "_link"
        existing_names.add(name.lower())

        col_l = f"{lt.name}_{left.name}"
        col_r = f"{rt.name}_{right.name}"
        if col_l == col_r:
            col_r += "_2"

        lines = [
            f"    {q(col_l)} {reference_type(left, dialect)} NOT NULL",
            f"    {q(col_r)} {reference_type(right, dialect)} NOT NULL",
            f"    CONSTRAINT {q(constraint_name('pk', name))} PRIMARY KEY ({q(col_l)}, {q(col_r)})",
            f"    CONSTRAINT {q(constraint_name('fk', name, col_l))} FOREIGN KEY ({q(col_l)}) "
            f"REFERENCES {q(lt.name)} ({q(left.name)}) ON DELETE CASCADE",
            f"    CONSTRAINT {q(constraint_name('fk', name, col_r))} FOREIGN KEY ({q(col_r)}) "
            f"REFERENCES {q(rt.name)} ({q(right.name)}) ON DELETE CASCADE",
        ]
        out.append(f"-- Junction table for the many-to-many relation {lt.name} <-> {rt.name}")
        out.append(f"CREATE TABLE {q(name)} (")
        out.append(",\n".join(lines))
        out.append(");")
        out.append("")

    # ---- 3. Les clés étrangères (PostgreSQL et MySQL) ----
    # On les ajoute APRÈS toutes les tables : ainsi l'ordre des CREATE TABLE
    # n'a pas d'importance, même si deux tables se référencent mutuellement.
    if not inline_fks and one_to_x:
        out.append("-- Foreign keys")
        for r in one_to_x:
            parent, child = fields_by_id[r.value_from], fields_by_id[r.value_to]
            c_table, p_table = table_of[child.id].name, table_of[parent.id].name
            out.append(
                f"ALTER TABLE {q(c_table)} ADD CONSTRAINT {q(constraint_name('fk', c_table, child.name))} "
                f"FOREIGN KEY ({q(child.name)}) REFERENCES {q(p_table)} ({q(parent.name)});"
            )
        out.append("")

    if dialect == "postgresql":
        out.append("COMMIT;")

    if not tables:
        out.append("-- This schema has no table.")

    return ExportResult(sql="\n".join(out).rstrip() + "\n", warnings=warnings)
