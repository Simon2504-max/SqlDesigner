/**
 * constants.js — Valeurs partagées par l'interface.
 * Elles doivent rester identiques à celles du serveur (backend/models.py).
 */

// Types SQL proposés pour les champs, regroupés pour la liste déroulante
export const SQL_TYPE_GROUPS = [
  { label: "Numbers", types: ["INT", "INTEGER", "SMALLINT", "BIGINT", "SERIAL", "DECIMAL", "NUMERIC", "FLOAT", "REAL", "DOUBLE"] },
  { label: "Text", types: ["CHAR", "VARCHAR", "TEXT"] },
  { label: "Date & time", types: ["DATE", "TIME", "TIMESTAMP", "DATETIME", "INTERVAL"] },
  { label: "Other", types: ["BOOLEAN", "UUID", "JSON", "JSONB", "ENUM", "ARRAY", "BINARY", "VARBINARY", "BLOB"] },
];

// Types qui acceptent une longueur : VARCHAR(100), DECIMAL(10)…
export const LENGTH_TYPES = ["CHAR", "VARCHAR", "BINARY", "VARBINARY", "DECIMAL", "NUMERIC"];

// Types de relations
export const RELATION_TYPES = [
  { value: "OM", label: "1 : N", help: "one-to-many — e.g. one author writes many books" },
  { value: "OO", label: "1 : 1", help: "one-to-one — e.g. one member has one card" },
  { value: "MM", label: "N : N", help: "many-to-many — e.g. books and categories" },
];

export const RELATION_LABEL = Object.fromEntries(RELATION_TYPES.map((r) => [r.value, r.label]));

// Dialectes SQL de l'export
export const DIALECTS = [
  { value: "postgresql", label: "PostgreSQL" },
  { value: "mysql", label: "MySQL" },
  { value: "sqlite", label: "SQLite" },
];
