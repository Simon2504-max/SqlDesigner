/**
 * FieldPanel.js — Les champs de la table sélectionnée : affichage, ajout,
 * modification, suppression, et relations de chaque champ.
 */
import React, { useState } from "react";
import { api } from "../api";
import { RELATION_LABEL } from "../constants";
import FieldForm from "./FieldForm";
import RelationDialog from "./RelationDialog";

/** Petites étiquettes PK / NN / UQ / défaut à côté d'un champ. */
function FieldBadges({ field }) {
  return (
    <span className="ed-badges">
      {field.is_primary_key && <span className="ed-badge ed-badge-pk" title="Primary key">PK</span>}
      {!field.is_primary_key && !field.is_nullable && <span className="ed-badge" title="NOT NULL">NN</span>}
      {field.is_unique && <span className="ed-badge" title="UNIQUE">UQ</span>}
      {field.default_value && (
        <span className="ed-badge ed-badge-default" title="Default value">
          = {field.default_value}
        </span>
      )}
    </span>
  );
}

export default function FieldPanel({ table, tables, fields, relations, run }) {
  const [editingId, setEditingId] = useState(null);
  const [relationFrom, setRelationFrom] = useState(null);

  const tableFields = fields
    .filter((f) => f.table === table.id)
    .sort((a, b) => a.position - b.position || a.name.localeCompare(b.name));

  const fieldById = Object.fromEntries(fields.map((f) => [f.id, f]));
  const tableName = (id) => tables.find((t) => t.id === id)?.name ?? "?";

  const deleteField = (field) => {
    if (!window.confirm(`Delete the field "${field.name}" and its relations?`)) return;
    run(() => api.deleteField(field.id), `Field "${field.name}" deleted.`);
  };

  return (
    <div className="ed-panel">
      <h4>
        Fields of <code>{table.name}</code>
      </h4>

      {tableFields.length === 0 && <p className="ed-muted">No field yet: add the first one below.</p>}

      <ul className="ed-list">
        {tableFields.map((f) => {
          const fieldRelations = relations.filter((r) => r.value_from === f.id || r.value_to === f.id);

          if (editingId === f.id) {
            return (
              <li key={f.id} className="ed-item ed-item-editing">
                <FieldForm
                  field={f}
                  submitLabel="Save"
                  onCancel={() => setEditingId(null)}
                  onSubmit={async (changes) => {
                    const ok = await run(() => api.updateField(f.id, changes), `Field "${changes.name}" saved.`);
                    if (ok) setEditingId(null);
                    return ok;
                  }}
                />
              </li>
            );
          }

          return (
            <li key={f.id} className="ed-item">
              <div className="ed-item-main">
                <span className="ed-field-name">{f.name}</span>
                <span className="ed-field-type">
                  {f.type}
                  {f.length ? `(${f.length})` : ""}
                </span>
                <FieldBadges field={f} />
                <span className="ed-spacer" />
                <button className="chip ghost" onClick={() => setEditingId(f.id)}>Edit</button>
                <button className="chip ghost" onClick={() => setRelationFrom(f)}>+ Relation</button>
                <button className="chip danger" onClick={() => deleteField(f)}>Delete</button>
              </div>

              {fieldRelations.length > 0 && (
                <ul className="ed-relations">
                  {fieldRelations.map((r) => {
                    const outgoing = r.value_from === f.id;
                    const other = fieldById[outgoing ? r.value_to : r.value_from];
                    return (
                      <li key={r.id}>
                        <span className="ed-rel-arrow">{outgoing ? "→" : "←"}</span>
                        <code>
                          {other ? `${tableName(other.table)}.${other.name}` : "?"}
                        </code>
                        <span className="ed-rel-type">{RELATION_LABEL[r.type] || r.type}</span>
                        <span className="ed-muted">
                          {outgoing ? "referenced by" : "references"}
                        </span>
                        <button
                          className="ed-icon-button"
                          title="Delete this relation"
                          onClick={() => run(() => api.deleteRelation(r.id), "Relation deleted.")}
                        >
                          ✕
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </li>
          );
        })}
      </ul>

      <div className="ed-add-box">
        <div className="ed-add-title">Add a field</div>
        <FieldForm
          submitLabel="Add field"
          onSubmit={(newField) =>
            run(() => api.createField({ ...newField, table: table.id }), `Field "${newField.name}" added.`)
          }
        />
      </div>

      {relationFrom && (
        <RelationDialog
          from={relationFrom}
          tables={tables}
          fields={fields}
          onClose={() => setRelationFrom(null)}
          onCreate={(relation) => run(() => api.createRelation(relation), "Relation added.")}
        />
      )}
    </div>
  );
}
