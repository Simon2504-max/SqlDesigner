/**
 * ExportDialog.js — Aperçu et téléchargement du script SQL, avec choix du dialecte
 * et affichage des avertissements calculés par le serveur.
 */
import React, { useEffect, useState } from "react";
import { api, downloadText } from "../api";
import { DIALECTS } from "../constants";
import { errorMessage } from "../session";

export default function ExportDialog({ schema, onClose }) {
  const [dialect, setDialect] = useState("postgresql");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setResult(null);
    setError("");
    api
      .getSql(schema.id, dialect)
      .then(setResult)
      .catch((err) => setError(errorMessage(err, "Export failed.")));
  }, [schema.id, dialect]);

  const copy = async () => {
    await navigator.clipboard.writeText(result.sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const fileName = `${schema.name.replace(/\s+/g, "_")}_${dialect}.sql`;

  return (
    <div className="ed-modal-overlay" onClick={onClose}>
      <div className="ed-modal ed-modal-wide" onClick={(e) => e.stopPropagation()}>
        <div className="ed-row">
          <h3 className="ed-grow">Export SQL — {schema.name}</h3>
          <div className="ed-tabs">
            {DIALECTS.map((d) => (
              <button
                key={d.value}
                className={`chip ${dialect === d.value ? "primary" : "secondary"}`}
                onClick={() => setDialect(d.value)}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>

        {error && <div className="ed-notice ed-notice-error">{error}</div>}

        {result?.warnings?.length > 0 && (
          <div className="ed-warnings">
            <strong>⚠ {result.warnings.length} warning(s)</strong>
            <ul>
              {result.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </div>
        )}

        <pre className="ed-code">{result ? result.sql : "Loading…"}</pre>

        <div className="ed-row ed-actions">
          <button className="chip primary" disabled={!result} onClick={() => downloadText(fileName, result.sql, "application/sql")}>
            Download {fileName}
          </button>
          <button className="chip secondary" disabled={!result} onClick={copy}>
            {copied ? "Copied ✓" : "Copy"}
          </button>
          <span className="ed-spacer" />
          <button className="chip secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
