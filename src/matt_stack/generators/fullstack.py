"""Fullstack monorepo generator (backend + frontend + optional iOS)."""

from __future__ import annotations

from collections.abc import Callable

from matt_stack.config import DeploymentTarget
from matt_stack.generators.base import BaseGenerator
from matt_stack.post_processors.b2b import print_b2b_instructions
from matt_stack.post_processors.customizer import customize_backend, customize_frontend
from matt_stack.post_processors.frontend_config import setup_frontend_monorepo
from matt_stack.templates.docker_compose import generate_docker_compose
from matt_stack.templates.docker_compose_override import generate_docker_compose_override
from matt_stack.templates.docker_compose_prod import generate_docker_compose_prod
from matt_stack.templates.pre_commit_config import generate_pre_commit_config
from matt_stack.templates.root_claude_md import generate_claude_md
from matt_stack.templates.root_env import generate_env_example
from matt_stack.templates.root_gitignore import generate_gitignore
from matt_stack.templates.root_makefile import generate_makefile
from matt_stack.templates.root_readme import generate_readme
from matt_stack.utils.console import print_error


class FullstackGenerator(BaseGenerator):
    """Generate a fullstack monorepo: backend + frontend + optional iOS."""

    @property
    def steps(self) -> list[tuple[str, Callable]]:
        steps: list[tuple[str, Callable]] = [
            ("Creating project directory", self._step_create_dir),
            ("Cloning backend", self._step_clone_backend),
            ("Cloning frontend", self._step_clone_frontend),
            ("Creating root files", self._step_create_root_files),
            ("Writing pre-commit config", self._write_pre_commit_config),
            ("Customizing backend", self._step_customize_backend),
            ("Customizing frontend", self._step_customize_frontend),
            ("Initializing git", self._step_init_git),
            ("Finishing up", self._step_finish),
        ]

        # Insert iOS clone step if needed
        if self.config.include_ios:
            steps.insert(3, ("Cloning iOS starter", self._step_clone_ios))

        return steps

    def _step_create_dir(self) -> bool:
        return self.create_root_directory()

    def _step_clone_backend(self) -> bool:
        return self.clone_and_strip(self.config.backend_repo_key, "backend")

    def _step_clone_frontend(self) -> bool:
        return self.clone_and_strip(self.config.frontend_repo_key, "frontend")

    def _step_clone_ios(self) -> bool:
        return self.clone_and_strip("swift-ios", "ios")

    def _step_create_root_files(self) -> bool:
        try:
            self.write_file("Makefile", generate_makefile(self.config))
            self.write_file("docker-compose.yml", generate_docker_compose(self.config))
            self.write_file("docker-compose.prod.yml", generate_docker_compose_prod(self.config))
            self.write_file(
                "docker-compose.override.yml.example",
                generate_docker_compose_override(self.config),
            )
            self.write_file(".env.example", generate_env_example(self.config))
            self.write_file(".env", generate_env_example(self.config))
            self.write_file("README.md", generate_readme(self.config))
            self.write_file("CLAUDE.md", generate_claude_md(self.config))
            self.write_file(".gitignore", generate_gitignore(self.config))
            self.write_file("tasks/todo.md", f"# {self.config.display_name} TODO\n")

            # Deployment configs
            if self.config.deployment == DeploymentTarget.RAILWAY:
                from matt_stack.templates.deploy_railway import (
                    generate_railway_json,
                    generate_railway_toml,
                )

                self.write_file("railway.json", generate_railway_json(self.config))
                self.write_file("railway.toml", generate_railway_toml(self.config))
            elif self.config.deployment == DeploymentTarget.RENDER:
                from matt_stack.templates.deploy_render import generate_render_yaml

                self.write_file("render.yaml", generate_render_yaml(self.config))
            # Vercel is always useful for frontend
            if self.config.has_frontend:
                from matt_stack.templates.deploy_vercel import generate_vercel_json

                self.write_file("vercel.json", generate_vercel_json(self.config))

            return True
        except OSError as e:
            print_error(f"Failed to create root files: {e}")
            return False

    def _write_pre_commit_config(self) -> bool:
        try:
            self.write_file(".pre-commit-config.yaml", generate_pre_commit_config(self.config))
            return True
        except OSError as e:
            print_error(f"Failed to write pre-commit config: {e}")
            return False

    def _step_customize_backend(self) -> bool:
        try:
            customize_backend(self.config)
            return True
        except Exception as e:
            print_error(f"Failed to customize backend: {e}")
            return False

    def _step_customize_frontend(self) -> bool:
        try:
            customize_frontend(self.config)
            setup_frontend_monorepo(self.config)
            return True
        except Exception as e:
            print_error(f"Failed to customize frontend: {e}")
            return False

    def _step_init_git(self) -> bool:
        return self.init_git_repository()

    def _step_finish(self) -> bool:
        if self.config.is_b2b:
            print_b2b_instructions(self.config)
        return True
