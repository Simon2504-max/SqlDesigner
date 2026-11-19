/**
 * DsdPanel.js — Affiche le diagramme entité-relation (Mermaid) du schéma.
 * Il se redessine tout seul quand le schéma change (prop "version").
 */
import React, { useEffect, useState } from "react";
import mermaid from "mermaid";
import { api, downloadText } from "../api";
import { errorMessage } from "../session";

mermaid.initialize({ startOnLoad: false, theme: "default", securityLevel: "strict" });

let renderCount = 0; // chaque dessin Mermaid a besoin d'un identifiant unique

export default function DsdPanel({ schema, version }) {
  const [code, setCode] = useState("");
  const [svg, setSvg] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false; // si le composant change entre-temps, on ignore le résultat
    setLoading(true);
    setError("");
    api
      .getDsd(schema.id)
      .then(async (text) => {
        renderCount += 1;
        const result = await mermaid.render(`dsd-${renderCount}`, text);
        if (!cancelled) {
          setCode(text);
          setSvg(result.svg);
        }
      })
      .catch((err) => {
        if (!cancelled) setError(err?.response ? errorMessage(err) : `Diagram error: ${err.message || err}`);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [schema.id, version]);

  const fileBase = schema.name.replace(/\s+/g, "_");

  return (
    <div className="ed-panel ed-dsd">
      <div className="ed-row">
        <h4 className="ed-grow">Entity-relationship diagram</h4>
        <button className="chip ghost" disabled={!svg} onClick={() => downloadText(`${fileBase}.svg`, svg, "image/svg+xml")}>
          Download SVG
        </button>
        <button className="chip ghost" disabled={!code} onClick={() => downloadText(`${fileBase}.mmd`, code)}>
          Download Mermaid
        </button>
      </div>
      {error && <div className="ed-notice ed-notice-error">{error}</div>}
      <div className="ed-dsd-canvas">
        {loading && !svg && <span className="ed-muted">Drawing…</span>}
        {svg && <div dangerouslySetInnerHTML={{ __html: svg }} />}
      </div>
    </div>
  );
}
