// vite.config.mjs — Configuration de Vite (l'outil qui lance et construit l'interface)
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()], // comprend le JSX et recharge les composants à chaud
  server: {
    port: 3000, // même port qu'avant : le backend n'autorise que http://localhost:3000 (CORS)
    open: true, // ouvre le navigateur au démarrage
  },
  preview: { port: 3000 },
  build: { outDir: "build" }, // même dossier de sortie qu'avec Create React App (utilisé par Docker)
});
