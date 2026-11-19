"""
diagram.py — Diagramme entité-relation (DSD) au format Mermaid.

Mermaid est une bibliothèque JavaScript qui dessine un diagramme à partir
d'un simple texte. L'interface reçoit ce texte et le transforme en image (SVG).

Exemple de texte produit :

    erDiagram
        auteur {
            INT id PK "NOT NULL"
            VARCHAR nom "NOT NULL, longueur 100"
        }
        livre {
            INT id PK "NOT NULL"
            INT auteur_id FK
        }
        auteur ||--o{ livre : "auteur_id"

Notation des relations ("pattes de corbeau") :
    ||--o|   un pour un           (1:1)
    ||--o{   un pour plusieurs    (1:N)
    }o--o{   plusieurs pour plusieurs (N:N)
"""
import re

# Symbole Mermaid pour chaque type de relation de l'application
CARDINALITY = {
    "OO": "||--o|",
    "OM": "||--o{",
    "MM": "}o--o{",
}


def safe_name(name: str) -> str:
    """Mermaid n'accepte que lettres, chiffres et _ dans les noms : on remplace le reste."""
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", str(name or "sans_nom"))
    return cleaned if cleaned[0].isalpha() else "t_" + cleaned


def safe_text(text: str) -> str:
    """Un commentaire Mermaid est entre guillemets : on retire les guillemets du texte."""
    return str(text).replace('"', "'")


def generate_er_diagram(schema) -> str:
    """Point d'entrée : produit le texte Mermaid d'un schéma (objet models.Schema)."""
    tables = list(schema.tables)
    fields_by_id = {f.id: f for t in tables for f in t.fields}
    table_of = {f.id: t for t in tables for f in t.fields}

    # Relations dont les deux champs sont dans ce schéma (chacune une seule fois)
    relations, seen = [], set()
    for f in fields_by_id.values():
        for r in f.relations_from:
            if r.value_to in fields_by_id and r.id not in seen:
                seen.add(r.id)
                relations.append(r)

    # Champs qui sont des clés étrangères (côté "plusieurs" d'une relation 1:1 ou 1:N)
    foreign_keys = {r.value_to for r in relations if r.type in ("OO", "OM")}

    lines = ["---", f"title: {safe_text(schema.name)}", "---", "erDiagram"]

    if not tables:
        lines += ["    SCHEMA_VIDE {", '        TEXT info "aucune table"', "    }"]
        return "\n".join(lines)

    # ---- Les entités (tables) et leurs attributs (champs) ----
    for t in tables:
        lines.append(f"    {safe_name(t.name)} {{")
        if not t.fields:
            lines.append('        TEXT vide "aucun champ"')
        for f in t.fields:
            keys = []
            if f.is_primary_key:
                keys.append("PK")
            if f.id in foreign_keys:
                keys.append("FK")
            if f.is_unique and not f.is_primary_key:
                keys.append("UK")

            notes = []
            if not f.is_nullable or f.is_primary_key:
                notes.append("NOT NULL")
            if f.length:
                notes.append(f"longueur {f.length}")
            if f.default_value:
                notes.append(f"défaut {f.default_value}")

            line = f"        {safe_name(f.type)} {safe_name(f.name)}"
            if keys:
                line += " " + ", ".join(keys)
            if notes:
                line += f' "{safe_text(", ".join(notes))}"'
            lines.append(line)
        lines.append("    }")

    # ---- Les relations ----
    for r in relations:
        parent, child = fields_by_id[r.value_from], fields_by_id[r.value_to]
        left = safe_name(table_of[parent.id].name)
        right = safe_name(table_of[child.id].name)
        symbol = CARDINALITY.get(r.type, "||--o{")
        label = "N:N" if r.type == "MM" else f"{child.name} -> {parent.name}"
        lines.append(f'    {left} {symbol} {right} : "{safe_text(label)}"')

    return "\n".join(lines)
