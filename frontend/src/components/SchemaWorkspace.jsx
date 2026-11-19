/**
 * SchemaWorkspace.js — L'espace de travail d'un schéma ouvert.
 *
 * Il charge les tables, champs et relations du schéma, puis les transmet aux
 * panneaux (TablePanel, FieldPanel) et aux fenêtres (EML, DSD, export SQL).
 *
 * La fonction run(action, message) est le cœur du composant : elle exécute une
 * modification (ajout, suppression…), affiche un message de succès ou d'erreur,
 * puis recharge les données pour que tout l'écran reste à jour.
 */
import React, { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { API_BASE } from "../session";
import EmlDialog from "../pages/EmlDialog";
import DsdPanel from "./DsdPanel";
import ExportDialog from "./ExportDialog";
import FieldPanel from "./FieldPanel";
import TablePanel from "./TablePanel";

export default function SchemaWorkspace({ schema, notify, fail }) {
  const [tables, setTables] = useState([]);
  const [fields, setFields] = useState([]);
  const [relations, setRelations] = useState([]);
  const [selectedTableId, setSelectedTableId] = useState(null);
  const [version, setVersion] = useState(0); // augmente à chaque rechargement (pour le DSD)
  const [showDsd, setShowDsd] = useState(false);
  const [emlOpen, setEmlOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);

  const reload = useCallback(async () => {
    const [t, f, r] = await Promise.all([
      api.listTables(schema.id),
      api.listFields(schema.id),
      api.listRelations(schema.id),
    ]);
    setTables(t);
    setFields(f);
    setRelations(r);
    setVersion((v) => v + 1);
  }, [schema.id]);

  // Chargement initial, et à chaque changement de schéma
  useEffect(() => {
    setSelectedTableId(null);
    reload().catch((err) => fail(err, "Could not load the schema."));
  }, [reload, fail]);

  const run = useCallback(
    async (action, successMessage) => {
      try {
        await action();
        if (successMessage) notify("success", successMessage);
        await reload();
        return true;
      } catch (err) {
        fail(err);
        return false;
      }
    },
    [notify, fail, reload]
  );

  const selectedTable = tables.find((t) => t.id === selectedTableId) || null;

  return (
    <section className="ed-workspace">
      <div className="ed-toolbar">
        <h3>{schema.name}</h3>
        <span className="ed-muted">
          {tables.length} tables · {fields.length} fields · {relations.length} relations
        </span>
        <span className="ed-spacer" />
        <button className="chip secondary" onClick={() => setEmlOpen(true)}>
          EML
        </button>
        <button className={`chip ${showDsd ? "primary" : "secondary"}`} onClick={() => setShowDsd((s) => !s)}>
          {showDsd ? "Hide DSD" : "DSD"}
        </button>
        <button className="chip primary" onClick={() => setExportOpen(true)}>
          Export SQL
        </button>
      </div>

      {showDsd && <DsdPanel schema={schema} version={version} />}

      <div className="ed-grid">
        <TablePanel
          schemaId={schema.id}
          tables={tables}
          fields={fields}
          selectedId={selectedTableId}
          onSelect={setSelectedTableId}
          run={run}
        />
        {selectedTable ? (
          <FieldPanel table={selectedTable} tables={tables} fields={fields} relations={relations} run={run} />
        ) : (
          <div className="ed-panel ed-placeholder">Select a table to see and edit its fields.</div>
        )}
      </div>

      <EmlDialog
        open={emlOpen}
        onClose={() => setEmlOpen(false)}
        schemaId={schema.id}
        schemaName={schema.name}
        apiBase={API_BASE}
      />
      {exportOpen && <ExportDialog schema={schema} onClose={() => setExportOpen(false)} />}
    </section>
  );
}
