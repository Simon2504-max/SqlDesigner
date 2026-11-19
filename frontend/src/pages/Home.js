/**
 * Home.js — La page principale : la liste des schémas de l'utilisateur
 * et l'espace de travail du schéma ouvert.
 *
 * Organisation de l'interface :
 *   Home
 *   └── SchemaManager          (liste des schémas)
 *       └── SchemaWorkspace    (schéma ouvert)
 *           ├── TablePanel     (tables)
 *           ├── FieldPanel     (champs + relations)
 *           │   ├── FieldForm
 *           │   └── RelationDialog
 *           ├── DsdPanel       (diagramme entité-relation)
 *           ├── EmlDialog      (diagramme interactif)
 *           └── ExportDialog   (export SQL)
 */
import React, { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import Notice from "../components/Notice";
import SchemaWorkspace from "../components/SchemaWorkspace";
import { errorMessage } from "../session";
import "../editor.css";

function SchemaManager() {
  const [schemas, setSchemas] = useState([]);
  const [openId, setOpenId] = useState(null);
  const [newName, setNewName] = useState("");
  const [notice, setNotice] = useState(null);

  // Messages : notify("success", "…") ou fail(erreur) pour une erreur du serveur
  const notify = useCallback((type, text) => setNotice({ type, text, at: Date.now() }), []);
  const fail = useCallback(
    (err, fallback) => setNotice({ type: "error", text: errorMessage(err, fallback), at: Date.now() }),
    []
  );
  const closeNotice = useCallback(() => setNotice(null), []);

  const loadSchemas = useCallback(
    () => api.listSchemas().then(setSchemas).catch((err) => fail(err, "Could not load your schemas.")),
    [fail]
  );

  useEffect(() => {
    loadSchemas();
  }, [loadSchemas]);

  const createSchema = async (e) => {
    e.preventDefault();
    const name = newName.trim();
    if (!name) return;
    try {
      const schema = await api.createSchema(name);
      setNewName("");
      await loadSchemas();
      setOpenId(schema.id);
      notify("success", `Schema "${name}" created.`);
    } catch (err) {
      fail(err);
    }
  };

  const renameSchema = async (schema) => {
    const name = window.prompt("New schema name:", schema.name);
    if (!name || name.trim() === schema.name) return;
    try {
      await api.renameSchema(schema.id, name.trim());
      await loadSchemas();
      notify("success", "Schema renamed.");
    } catch (err) {
      fail(err);
    }
  };

  const deleteSchema = async (schema) => {
    if (!window.confirm(`Delete the schema "${schema.name}" and everything in it?`)) return;
    try {
      await api.deleteSchema(schema.id);
      if (openId === schema.id) setOpenId(null);
      await loadSchemas();
      notify("success", `Schema "${schema.name}" deleted.`);
    } catch (err) {
      fail(err);
    }
  };

  const openSchema = schemas.find((s) => s.id === openId) || null;

  return (
    <div className="ed-root">
      <Notice notice={notice} onClose={closeNotice} />

      <h2>My Schemas</h2>
      <form className="ed-row" onSubmit={createSchema}>
        <input
          className="small-input ed-grow"
          placeholder="New schema name"
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
        />
        <button className="chip primary" disabled={!newName.trim()}>
          Create schema
        </button>
      </form>

      {schemas.length === 0 && <p className="ed-muted">You have no schema yet.</p>}

      <ul className="ed-list ed-schema-list">
        {schemas.map((s) => (
          <li key={s.id} className={`ed-item ${openId === s.id ? "selected" : ""}`}>
            <div className="ed-item-main">
              <span className="ed-field-name">{s.name}</span>
              <span className="ed-spacer" />
              <button
                className={`chip ${openId === s.id ? "ghost" : "secondary"}`}
                onClick={() => setOpenId(openId === s.id ? null : s.id)}
              >
                {openId === s.id ? "Close" : "Open"}
              </button>
              <button className="chip ghost" onClick={() => renameSchema(s)}>
                Rename
              </button>
              <button className="chip danger" onClick={() => deleteSchema(s)}>
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>

      {openSchema && <SchemaWorkspace key={openSchema.id} schema={openSchema} notify={notify} fail={fail} />}
    </div>
  );
}

export default function Home({ onOpenProfile, onLogout }) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">SqlDesigner</div>
        <div className="header-actions">
          <button className="ghost" onClick={onOpenProfile}>
            Profile
          </button>
          <button className="secondary" onClick={onLogout}>
            Log out
          </button>
        </div>
      </header>
      <main className="home-main">
        <section className="hero">
          <SchemaManager />
        </section>
      </main>
    </div>
  );
}
