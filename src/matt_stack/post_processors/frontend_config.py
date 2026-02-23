"""Post-processor to configure frontend for monorepo integration."""

from __future__ import annotations

from matt_stack.config import ProjectConfig
from matt_stack.utils.console import print_info


def setup_frontend_monorepo(config: ProjectConfig) -> None:
    """Configure frontend .env for monorepo mode with Django backend."""
    if not config.has_frontend or not config.has_backend:
        return

    env_file = config.frontend_dir / ".env"
    env_content = """\
VITE_MODE=django-spa
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_AUTH_TOKEN_KEY=access_token
VITE_REFRESH_TOKEN_KEY=refresh_token
VITE_ENABLE_MOCK_API=false
VITE_DJANGO_CSRF_TOKEN_NAME=csrftoken
VITE_DJANGO_STATIC_URL=/static/
VITE_DJANGO_MEDIA_URL=/media/
VITE_DJANGO_API_PREFIX=/api/v1
"""
    env_file.write_text(env_content)

    # Also create .env.monorepo as a reference
    env_mono = config.frontend_dir / ".env.monorepo"
    env_mono.write_text(env_content)

    print_info("Configured frontend for monorepo mode")

    _create_vite_monorepo_config(config)


def _create_vite_monorepo_config(config: ProjectConfig) -> None:
    """Create vite.config.monorepo.ts with Django proxy settings."""
    vite_config = config.frontend_dir / "vite.config.monorepo.ts"
    vite_config.write_text("""\
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/static": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/media": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/admin": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "dist",
    rollupOptions: {
      output: {
        assetFileNames: "static/css/[name]-[hash][extname]",
        chunkFileNames: "static/js/[name]-[hash].js",
        entryFileNames: "static/js/[name]-[hash].js",
      },
    },
  },
});
""")
    print_info("Created vite.config.monorepo.ts with Django proxy")
