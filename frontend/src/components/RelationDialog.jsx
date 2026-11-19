/**
 * RelationDialog.js — Fenêtre pour ajouter une relation à partir d'un champ.
 *
 * Convention : le champ de départ ("from") est le champ RÉFÉRENCÉ (côté "un",
 * en général une clé primaire comme author.id) ; le champ d'arrivée ("to") est
 * la CLÉ ÉTRANGÈRE (ex. book.author_id).
 */
import React, { useState } from "react";
import { RELATION_TYPES } from "../constants";

export default function RelationDialog({ from, tables, fields, onClose, onCreate }) {
  const [toId, setToId] = useState("");
  const [type, setType] = useState("OM");
  const [saving, setSaving] = useState(false);

  const fromTable = tables.find((t) => t.id === from.table);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    const ok = await onCreate({ value_from: from.id, value_to: toId, type });
    setSaving(false);
    if (ok) onClose();
  };

  return (
    <div className="ed-modal-overlay" onClick={onClose}>
      <form className="ed-modal" onClick={(e) => e.stopPropagation()} onSubmit={handleSubmit}>
        <h3>
          New relation from <code>{fromTable?.name}.{from.name}</code>
        </h3>
        <p className="ed-help">
          The field you start from is the <strong>referenced</strong> one (usually a primary key, e.g.{" "}
          <code>author.id</code>). Pick the <strong>foreign key</strong> that points to it (e.g.{" "}
          <code>book.author_id</code>).
        </p>

        <label className="ed-label">Foreign key field</label>
        <select className="small-input ed-full" value={toId} onChange={(e) => setToId(e.target.value)} autoFocus>
          <option value="">— choose a field —</option>
          {tables.map((t) => {
            const options = fields.filter((f) => f.table === t.id && f.id !== from.id);
            if (options.length === 0) return null;
            return (
              <optgroup key={t.id} label={t.name}>
                {options.map((f) => (
                  <option key={f.id} value={f.id}>
                    {t.name}.{f.name} ({f.type})
                  </option>
                ))}
              </optgroup>
            );
          })}
        </select>

        <label className="ed-label">Type</label>
        <div className="ed-radio-list">
          {RELATION_TYPES.map((r) => (
            <label key={r.value} className={type === r.value ? "active" : ""}>
              <input type="radio" name="type" value={r.value} checked={type === r.value} onChange={() => setType(r.value)} />
              <strong>{r.label}</strong> <span>{r.help}</span>
            </label>
          ))}
        </div>

        <div className="ed-row ed-actions">
          <button className="chip primary" disabled={!toId || saving}>
            {saving ? "Adding…" : "Add relation"}
          </button>
          <button type="button" className="chip secondary" onClick={onClose}>
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
