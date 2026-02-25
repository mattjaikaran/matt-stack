"""Vercel deployment config template."""

from __future__ import annotations

import json

from matt_stack.config import ProjectConfig


def generate_vercel_json(config: ProjectConfig) -> str:
    """Generate vercel.json for frontend SPA deployment."""
    vercel_config: dict = {
        "$schema": "https://openapi.vercel.sh/vercel.json",
        "buildCommand": "bun install && bun run build",
        "outputDirectory": "dist",
        "framework": "vite",
    }

    rewrites: list[dict] = []

    # Proxy API requests to the backend if this is a fullstack project
    if config.has_backend:
        rewrites.append({
            "source": "/api/:path*",
            "destination": "${VITE_API_BASE_URL}/api/:path*",
        })

    # SPA fallback: all unmatched routes serve index.html
    rewrites.append({
        "source": "/(.*)",
        "destination": "/index.html",
    })

    vercel_config["rewrites"] = rewrites

    # Headers for security
    vercel_config["headers"] = [
        {
            "source": "/(.*)",
            "headers": [
                {"key": "X-Frame-Options", "value": "SAMEORIGIN"},
                {"key": "X-Content-Type-Options", "value": "nosniff"},
            ],
        }
    ]

    return json.dumps(vercel_config, indent=2) + "\n"
