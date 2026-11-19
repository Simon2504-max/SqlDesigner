/**
 * api.js — Toutes les requêtes vers le serveur, au même endroit.
 *
 * Les composants appellent ces fonctions au lieu d'écrire les adresses eux-mêmes.
 * Le jeton de connexion est ajouté automatiquement (voir session.js).
 */
import axios from "axios";
import { API_BASE } from "./session";

const url = (path) => `${API_BASE}${path}`;
const data = (response) => response.data;

export const api = {
  // Schémas
  listSchemas: () => axios.get(url("/schemas/")).then(data),
  createSchema: (name) => axios.post(url("/schemas/"), { name }).then(data),
  renameSchema: (id, name) => axios.put(url(`/schemas/${id}`), { name }).then(data),
  deleteSchema: (id) => axios.delete(url(`/schemas/${id}`)),

  // Tables
  listTables: (schemaId) => axios.get(url(`/tables/schema/${schemaId}`)).then(data),
  createTable: (schemaId, name) => axios.post(url("/tables/"), { schema: schemaId, name }).then(data),
  renameTable: (id, name) => axios.put(url(`/tables/${id}`), { name }).then(data),
  deleteTable: (id) => axios.delete(url(`/tables/${id}`)),

  // Champs
  listFields: (schemaId) => axios.get(url(`/fields/schema/${schemaId}`)).then(data),
  createField: (field) => axios.post(url("/fields/"), field).then(data),
  updateField: (id, changes) => axios.put(url(`/fields/${id}`), changes).then(data),
  deleteField: (id) => axios.delete(url(`/fields/${id}`)),

  // Relations
  listRelations: (schemaId) => axios.get(url("/relations/"), { params: { schema_id: schemaId } }).then(data),
  createRelation: (relation) => axios.post(url("/relations/"), relation).then(data),
  deleteRelation: (id) => axios.delete(url(`/relations/${id}`)),

  // Diagramme et SQL
  getDsd: (schemaId) => axios.get(url(`/schemas/${schemaId}/dsd`), { responseType: "text" }).then(data),
  getSql: (schemaId, dialect) => axios.get(url(`/schemas/${schemaId}/sql`), { params: { dialect } }).then(data),
};

/** Fait télécharger un texte au navigateur, sous forme de fichier. */
export function downloadText(filename, text, mime = "text/plain") {
  const blob = new Blob([text], { type: `${mime};charset=utf-8` });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  URL.revokeObjectURL(link.href);
}
