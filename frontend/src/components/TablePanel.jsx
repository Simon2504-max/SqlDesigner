/**
 * TablePanel.js — La liste des tables d'un schéma : sélection, ajout,
 * renommage et suppression.
 */
import React, { useState } from "react";
import { api } from "../api";

export default function TablePanel({ schemaId, tables, fields, selectedId, onSelect, run }) {
  const [newName, setNewName] = useState("");

  const countFields = (tableId) => fields.filter((f) => f.table === tableId).length;

  const addTable = async (e) => {
    e.preventDefault();
    const name = newName.trim();
    if (!name) return;
    const ok = await run(async () => {
      const table = await api.createTable(schemaId, name);
      onSelect(table.id); // on ouvre directement la nouvelle table
    }, `Table "${name}" added.`);
    if (ok) setNewName("");
  };

  const renameTable = (table) => {
    const name = window.prompt("New table name:", table.name);
    if (!name || name.trim() === table.name) return;
    run(() => api.renameTable(table.id, name.trim()), "Table renamed.");
  };

  const deleteTable = async (table) => {
    if (!window.confirm(`Delete the table "${table.name}" with all its fields and relations?`)) return;
    const ok = await run(() => api.deleteTable(table.id), `Table "${table.name}" deleted.`);
    if (ok && selectedId === table.id) onSelect(null);
  };

  return (
    <div className="ed-panel">
      <h4>Tables ({tables.length})</h4>

      {tables.length === 0 && <p className="ed-muted">No table yet: add the first one below.</p>}

      <ul className="ed-list">
        {tables.map((t) => (
          <li
            key={t.id}
            className={`ed-item ed-table-item ${selectedId === t.id ? "selected" : ""}`}
            onClick={() => onSelect(t.id)}
          >
            <div className="ed-item-main">
              <span className="ed-field-name">{t.name}</span>
              <span className="ed-muted">{countFields(t.id)} fields</span>
              <span className="ed-spacer" />
              {/* stopPropagation : le clic sur un bouton ne doit pas aussi sélectionner la table */}
              <button className="chip ghost" onClick={(e) => { e.stopPropagation(); renameTable(t); }}>
                Rename
              </button>
              <button className="chip danger" onClick={(e) => { e.stopPropagation(); deleteTable(t); }}>
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>

      <form className="ed-row" onSubmit={addTable}>
        <input
          className="small-input ed-grow"
          placeholder="new_table_name"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
        />
        <button className="chip primary" disabled={!newName.trim()}>
          Add table
        </button>
      </form>
    </div>
  );
}
