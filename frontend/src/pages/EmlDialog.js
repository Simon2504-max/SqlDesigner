/**
 * EmlDialog.js — Diagramme interactif des tables d'un schéma (EML).
 *
 * Fonctionnement :
 *  1. À chaque ouverture, on recharge les tables, champs et relations du schéma
 *     depuis le serveur (les données sont donc toujours à jour).
 *  2. On transforme ces données en "nœuds" (les tables) et "arêtes" (les relations)
 *     pour React Flow, la bibliothèque qui dessine le diagramme.
 *  3. Dagre calcule automatiquement la position de chaque table pour éviter
 *     qu'elles se chevauchent.
 */
import React, { useCallback, useEffect, useState } from "react";
import axios from "axios";
import ReactFlow, {
  Background,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  useEdgesState,
  useNodesState,
} from "reactflow";
import dagre from "dagre";
import "reactflow/dist/style.css";

// Dimensions utilisées pour calculer la mise en page (en pixels)
const NODE_WIDTH = 260;
const HEADER_HEIGHT = 40;
const ROW_HEIGHT = 28;
const BODY_PADDING = 12;

const RELATION_LABELS = { OO: "1 : 1", OM: "1 : N", MM: "N : N" };

/** Hauteur réelle d'une table selon son nombre de champs. */
function nodeHeight(fieldCount) {
  return HEADER_HEIGHT + BODY_PADDING + Math.max(fieldCount, 1) * ROW_HEIGHT;
}

/** Calcule la position de chaque table avec Dagre (graphe neuf à chaque fois). */
function layout(nodes, edges) {
  const graph = new dagre.graphlib.Graph();
  graph.setDefaultEdgeLabel(() => ({}));
  graph.setGraph({ rankdir: "LR", nodesep: 60, ranksep: 140, marginx: 20, marginy: 20 });

  nodes.forEach((node) => {
    graph.setNode(node.id, { width: NODE_WIDTH, height: nodeHeight(node.data.fields.length) });
  });
  edges.forEach((edge) => graph.setEdge(edge.source, edge.target));

  dagre.layout(graph);

  return nodes.map((node) => {
    const { x, y } = graph.node(node.id);
    const height = nodeHeight(node.data.fields.length);
    // Dagre donne le centre de la table ; React Flow attend le coin en haut à gauche.
    return { ...node, position: { x: x - NODE_WIDTH / 2, y: y - height / 2 } };
  });
}

/** Petit badge (PK, NN, UQ) affiché à droite d'un champ. */
function Badge({ children, title }) {
  return (
    <span className="eml-badge" title={title}>
      {children}
    </span>
  );
}

/** Dessin d'une table : un en-tête et une ligne par champ. */
function TableNode({ data }) {
  return (
    <div className="eml-table" style={{ width: NODE_WIDTH }}>
      <div className="eml-table-header">{data.name}</div>
      <div className="eml-table-body">
        {data.fields.length === 0 && <div className="eml-empty">aucun champ</div>}
        {data.fields.map((field) => (
          <div key={field.id} className="eml-row">
            {/* Point d'arrivée d'une flèche (à gauche du champ) */}
            <Handle type="target" position={Position.Left} id={`${field.id}-t`} className="eml-handle" />

            <span className="eml-field-name">
              {field.is_primary_key && "🔑 "}
              {field.name}
            </span>
            <span className="eml-field-type">
              {field.type}
              {field.length ? `(${field.length})` : ""}
              {field.is_primary_key && <Badge title="Clé primaire">PK</Badge>}
              {!field.is_primary_key && !field.is_nullable && <Badge title="NOT NULL">NN</Badge>}
              {field.is_unique && <Badge title="UNIQUE">UQ</Badge>}
            </span>

            {/* Point de départ d'une flèche (à droite du champ) */}
            <Handle type="source" position={Position.Right} id={`${field.id}-s`} className="eml-handle" />
          </div>
        ))}
      </div>
    </div>
  );
}

// Défini en dehors du composant pour que React Flow ne le recrée pas à chaque rendu
const nodeTypes = { table: TableNode };

/** Récupère une liste ; un 404 du serveur signifie simplement "liste vide". */
async function getList(url) {
  try {
    const res = await axios.get(url);
    return res.data || [];
  } catch (err) {
    if (err?.response?.status === 404) return [];
    throw err;
  }
}

export default function EmlDialog({ open, onClose, schemaId, schemaName, apiBase }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [version, setVersion] = useState(0); // force React Flow à recadrer après chaque chargement

  const load = useCallback(async () => {
    if (!schemaId) return;
    setLoading(true);
    setError(null);
    try {
      const [tables, fields, relations] = await Promise.all([
        getList(`${apiBase}/tables/schema/${schemaId}`),
        getList(`${apiBase}/fields/schema/${schemaId}`),
        getList(`${apiBase}/relations/`),
      ]);

      // Champs regroupés par table, et table de chaque champ
      const fieldsByTable = {};
      const tableOfField = {};
      fields.forEach((f) => {
        if (!fieldsByTable[f.table]) fieldsByTable[f.table] = [];
        fieldsByTable[f.table].push(f);
        tableOfField[f.id] = f.table;
      });
      Object.values(fieldsByTable).forEach((list) =>
        list.sort((a, b) => (a.position ?? 0) - (b.position ?? 0) || a.name.localeCompare(b.name))
      );

      // 1. Les nœuds : une table = un nœud
      const newNodes = tables.map((t) => ({
        id: String(t.id),
        type: "table",
        position: { x: 0, y: 0 },
        data: { name: t.name, fields: fieldsByTable[t.id] || [] },
      }));

      // 2. Les arêtes : seulement les relations dont les deux champs sont dans ce schéma
      const newEdges = relations
        .filter((r) => tableOfField[r.value_from] && tableOfField[r.value_to])
        .map((r) => ({
          id: String(r.id),
          source: String(tableOfField[r.value_from]),
          sourceHandle: `${r.value_from}-s`,
          target: String(tableOfField[r.value_to]),
          targetHandle: `${r.value_to}-t`,
          type: "smoothstep",
          label: RELATION_LABELS[r.type] || r.type,
          markerEnd: { type: MarkerType.ArrowClosed, color: "#60a5fa" },
          style: { stroke: "#60a5fa", strokeWidth: 2 },
          labelStyle: { fill: "#e2e8f0", fontWeight: 700, fontSize: 12 },
          labelBgStyle: { fill: "#0f172a" },
          labelBgPadding: [6, 3],
          labelBgBorderRadius: 4,
        }));

      // 3. La mise en page
      setNodes(layout(newNodes, newEdges));
      setEdges(newEdges);
      setVersion((v) => v + 1);
    } catch (err) {
      console.error(err);
      setError("Impossible de charger le diagramme. Le serveur est-il lancé ?");
    } finally {
      setLoading(false);
    }
  }, [schemaId, apiBase, setNodes, setEdges]);

  // Recharge à chaque ouverture
  useEffect(() => {
    if (open) load();
  }, [open, load]);

  if (!open) return null;

  return (
    <div className="eml-overlay" onClick={onClose}>
      <div className="eml-dialog" onClick={(e) => e.stopPropagation()}>
        <style>{EML_CSS}</style>

        <div className="eml-header">
          <h2>{schemaName || "Diagramme"}</h2>
          <div className="eml-actions">
            <button onClick={load} disabled={loading}>
              {loading ? "Chargement…" : "Actualiser"}
            </button>
            <button onClick={onClose}>Fermer</button>
          </div>
        </div>

        <div className="eml-canvas">
          {error && <div className="eml-message eml-error">{error}</div>}
          {!error && !loading && nodes.length === 0 && (
            <div className="eml-message">Ce schéma ne contient encore aucune table.</div>
          )}
          <ReactFlow
            key={version}
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.2 }}
            minZoom={0.1}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#1e293b" gap={16} />
            <Controls />
            <MiniMap pannable zoomable nodeColor="#334155" maskColor="rgba(2,6,23,0.7)" />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}

// Styles du diagramme. Tous les noms commencent par "eml-" pour ne pas
// entrer en conflit avec les styles du reste de l'application (App.css).
const EML_CSS = `
.eml-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.75); display: flex;
  align-items: center; justify-content: center; z-index: 1000; }
.eml-dialog { background: #0f172a; width: 92%; height: 90%; border-radius: 12px; padding: 16px;
  display: flex; flex-direction: column; border: 1px solid #1e293b; }
.eml-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.eml-header h2 { margin: 0; color: #fff; font-size: 1.2rem; }
.eml-actions { display: flex; gap: 8px; }
.eml-actions button { background: transparent; border: 1px solid #475569; color: #cbd5e1;
  padding: 6px 12px; border-radius: 6px; cursor: pointer; }
.eml-actions button:hover { background: #334155; color: #fff; }
.eml-canvas { flex: 1; position: relative; background: #020617; border-radius: 8px; overflow: hidden; }
.eml-message { position: absolute; top: 16px; left: 50%; transform: translateX(-50%); z-index: 5;
  color: #94a3b8; background: #0f172a; padding: 8px 14px; border-radius: 6px; }
.eml-error { color: #fca5a5; }

.eml-table { background: #1e293b; border: 1px solid #334155; border-radius: 8px;
  font-family: system-ui, sans-serif; box-shadow: 0 4px 12px rgba(0,0,0,.4); }
.eml-table-header { height: ${HEADER_HEIGHT}px; line-height: ${HEADER_HEIGHT}px; text-align: center;
  background: #0b1220; color: #f1f5f9; font-weight: 700; font-size: 14px;
  border-bottom: 1px solid #334155; border-radius: 8px 8px 0 0;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; padding: 0 10px; }
.eml-table-body { padding: ${BODY_PADDING / 2}px 0; }
.eml-row { position: relative; height: ${ROW_HEIGHT}px; display: flex; align-items: center;
  justify-content: space-between; gap: 8px; padding: 0 14px; font-size: 12px; color: #cbd5e1; }
.eml-row + .eml-row { border-top: 1px solid #263244; }
.eml-field-name { font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.eml-field-type { color: #94a3b8; white-space: nowrap; display: flex; align-items: center; gap: 4px; }
.eml-badge { font-size: 9px; font-weight: 700; color: #0f172a; background: #fbbf24;
  border-radius: 3px; padding: 1px 3px; }
.eml-empty { height: ${ROW_HEIGHT}px; line-height: ${ROW_HEIGHT}px; text-align: center;
  color: #64748b; font-size: 12px; font-style: italic; }
.eml-handle { width: 8px !important; height: 8px !important; background: #60a5fa !important;
  border: 2px solid #1e293b !important; }
`;