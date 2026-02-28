"""Cloudflare Pages/Workers deployment config templates."""

from __future__ import annotations

from matt_stack.config import ProjectConfig


def generate_wrangler_toml(config: ProjectConfig) -> str:
    """Generate wrangler.toml for Cloudflare Pages deployment."""
    lines: list[str] = [
        f'name = "{config.name}"',
    ]

    if config.has_frontend and not config.has_backend:
        lines.extend(
            [
                'pages_build_output_dir = "frontend/dist"',
                "",
                "[build]",
                'command = "cd frontend && bun install && bun run build"',
            ]
        )
        if config.is_nextjs:
            lines[-2] = "[build]"
            lines[-1] = 'command = "cd frontend && bun install && bun run build"'
            lines[1] = 'pages_build_output_dir = "frontend/.next/static"'
    elif config.has_backend and config.has_frontend:
        lines.extend(
            [
                "",
                "# Frontend (Cloudflare Pages)",
                "# Deploy frontend/ as a Cloudflare Pages project.",
                "# Backend should be deployed separately (Docker, VPS, etc).",
                "",
                "# To deploy frontend to Cloudflare Pages:",
                f"#   cd frontend && npx wrangler pages deploy "
                f"{'out' if config.is_nextjs else 'dist'}",
                "",
                "[vars]",
            ]
        )
        if config.is_nextjs:
            lines.append(
                f'NEXT_PUBLIC_API_BASE_URL = "https://{config.name}-api.example.com/api/v1"'
            )
        else:
            lines.append(f'VITE_API_BASE_URL = "https://{config.name}-api.example.com/api/v1"')
    elif config.has_backend:
        lines.extend(
            [
                'compatibility_date = "2024-01-01"',
                "",
                "# Cloudflare Workers for backend API proxy or edge functions.",
                "# For full Django deployment, use Docker on a VPS/cloud provider",
                "# and put Cloudflare in front as CDN + proxy.",
                "",
                "[vars]",
                f'API_ORIGIN = "https://{config.name}-api.example.com"',
            ]
        )

    return "\n".join(lines) + "\n"
