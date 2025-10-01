import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "dist", // asegúrate que se genere en frontend/dist
  },
  base: './', // Importante para rutas relativas en producción
});
