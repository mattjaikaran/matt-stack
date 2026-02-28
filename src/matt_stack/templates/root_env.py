"""Root .env.example template for generated projects."""

from __future__ import annotations

from matt_stack.config import ProjectConfig


def generate_env_example(config: ProjectConfig) -> str:
    """Generate .env.example with combined backend + frontend vars."""
    lines: list[str] = ["# Project: " + config.display_name, ""]

    if config.has_backend:
        lines.extend(
            [
                "# === Backend ===",
                "DEBUG=true",
                f"DJANGO_SECRET_KEY=change-me-{config.name}-secret",
                f"POSTGRES_DB={config.python_package_name}",
                "POSTGRES_USER=postgres",
                "POSTGRES_PASSWORD=postgres",
                f"DATABASE_URL=postgres://postgres:postgres@localhost:5432/{config.python_package_name}",
                "ALLOWED_HOSTS=localhost,127.0.0.1",
                "CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173",
                "",
            ]
        )

        if config.use_redis:
            lines.extend(
                [
                    "# Redis",
                    "REDIS_URL=redis://localhost:6379/0",
                    "",
                ]
            )

        if config.use_celery:
            lines.extend(
                [
                    "# Celery",
                    "CELERY_BROKER_URL=redis://localhost:6379/0",
                    "CELERY_RESULT_BACKEND=redis://localhost:6379/0",
                    "",
                ]
            )

    if config.has_frontend:
        if config.is_nextjs:
            lines.extend(
                [
                    "# === Frontend (Next.js) ===",
                    "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1",
                    "NEXT_PUBLIC_AUTH_TOKEN_KEY=access_token",
                    "NEXT_PUBLIC_REFRESH_TOKEN_KEY=refresh_token",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "# === Frontend ===",
                    "VITE_API_BASE_URL=http://localhost:8000/api/v1",
                    "VITE_MODE=django-spa",
                    "VITE_AUTH_TOKEN_KEY=access_token",
                    "VITE_REFRESH_TOKEN_KEY=refresh_token",
                    "",
                ]
            )

    lines.extend(
        [
            "# === Ports ===",
            "API_PORT=8000",
            "FRONTEND_PORT=3000",
            "DB_PORT=5432",
            "REDIS_PORT=6379",
        ]
    )

    return "\n".join(lines) + "\n"
