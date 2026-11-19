/**
 * FieldForm.js — Formulaire d'un champ, utilisé pour l'AJOUT et pour la MODIFICATION.
 *
 * Il gère : nom, type, longueur, clé primaire, NOT NULL, UNIQUE, valeur par défaut.
 * onSubmit(données) doit renvoyer une promesse qui vaut true si l'enregistrement a réussi.
 */
import React, { useState } from "react";
import { LENGTH_TYPES, SQL_TYPE_GROUPS } from "../constants";

const EMPTY = {
  name: "",
  type: "VARCHAR",
  length: "",
  is_primary_key: false,
  not_null: false,
  is_unique: false,
  default_value: "",
};

/** Transforme un champ venu du serveur en valeurs du formulaire. */
function toFormValues(field) {
  if (!field) return EMPTY;
  return {
    name: field.name,
    type: field.type,
    length: field.length ?? "",
    is_primary_key: field.is_primary_key,
    not_null: !field.is_nullable,
    is_unique: field.is_unique,
    default_value: field.default_value ?? "",
  };
}

export default function FieldForm({ field, submitLabel, onSubmit, onCancel }) {
  const [values, setValues] = useState(() => toFormValues(field));
  const [saving, setSaving] = useState(false);

  const set = (key) => (e) => {
    const value = e.target.type === "checkbox" ? e.target.checked : e.target.value;
    setValues((v) => ({ ...v, [key]: value }));
  };

  const acceptsLength = LENGTH_TYPES.includes(values.type);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!values.name.trim()) return;
    setSaving(true);
    const ok = await onSubmit({
      name: values.name.trim(),
      type: values.type,
      length: acceptsLength && values.length !== "" ? Number(values.length) : null,
      is_primary_key: values.is_primary_key,
      is_nullable: values.is_primary_key ? false : !values.not_null,
      is_unique: values.is_unique,
      default_value: values.default_value.trim() || null,
    });
    setSaving(false);
    if (ok && !field) setValues(EMPTY); // après un ajout réussi, on vide le formulaire
  };

  return (
    <form className="ed-field-form" onSubmit={handleSubmit}>
      <div className="ed-row">
        <input
          className="small-input ed-grow"
          placeholder="field_name"
          value={values.name}
          onChange={set("name")}
          autoFocus={Boolean(field)}
        />
        <select className="small-input" value={values.type} onChange={set("type")}>
          {SQL_TYPE_GROUPS.map((group) => (
            <optgroup key={group.label} label={group.label}>
              {group.types.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </optgroup>
          ))}
        </select>
        {acceptsLength && (
          <input
            className="small-input ed-length"
            type="number"
            min="1"
            placeholder="length"
            value={values.length}
            onChange={set("length")}
          />
        )}
      </div>

      <div className="ed-row ed-options">
        <label title="Primary key: identifies each row (always NOT NULL)">
          <input type="checkbox" checked={values.is_primary_key} onChange={set("is_primary_key")} /> PK
        </label>
        <label title="NOT NULL: the value is required">
          <input
            type="checkbox"
            checked={values.is_primary_key || values.not_null}
            disabled={values.is_primary_key}
            onChange={set("not_null")}
          />{" "}
          NOT NULL
        </label>
        <label title="UNIQUE: no two rows can have the same value">
          <input type="checkbox" checked={values.is_unique} onChange={set("is_unique")} /> UNIQUE
        </label>
        <input
          className="small-input ed-grow"
          placeholder="default value (optional)"
          value={values.default_value}
          onChange={set("default_value")}
        />
      </div>

      <div className="ed-row ed-actions">
        <button className="chip primary" disabled={saving || !values.name.trim()}>
          {saving ? "Saving…" : submitLabel}
        </button>
        {onCancel && (
          <button type="button" className="chip secondary" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}
