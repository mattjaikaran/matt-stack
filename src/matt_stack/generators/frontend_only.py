"""Frontend-only project generator."""

from __future__ import annotations

from collections.abc import Callable

from matt_stack.config import DeploymentTarget
from matt_stack.generators.base import BaseGenerator
from matt_stack.post_processors.customizer import customize_frontend
from matt_stack.templates.cursorrules import generate_cursorrules
from matt_stack.templates.pre_commit_config import generate_pre_commit_config
from matt_stack.templates.root_gitignore import generate_gitignore
from matt_stack.templates.root_makefile import generate_makefile
from matt_stack.templates.root_readme import generate_readme
from matt_stack.utils.console import print_error


class FrontendOnlyGenerator(BaseGenerator):
    """Generate a frontend-only project."""

    @property
    def steps(self) -> list[tuple[str, Callable]]:
        return [
            ("Creating project directory", self._step_create_dir),
            ("Cloning frontend", self._step_clone_frontend),
            ("Creating root files", self._step_create_root_files),
            ("Writing pre-commit config", self._write_pre_commit_config),
            ("Customizing frontend", self._step_customize_frontend),
            ("Initializing git", self._step_init_git),
        ]

    def _step_create_dir(self) -> bool:
        return self.create_root_directory()

    def _step_clone_frontend(self) -> bool:
        return self.clone_and_strip(self.config.frontend_repo_key, "frontend")

    def _step_create_root_files(self) -> bool:
        try:
            self.write_file("Makefile", generate_makefile(self.config))
            self.write_file("README.md", generate_readme(self.config))
            self.write_file(".cursorrules", generate_cursorrules(self.config))
            self.write_file(".gitignore", generate_gitignore(self.config))

            if self.config.deployment == DeploymentTarget.FLY_IO:
                from matt_stack.templates.deploy_fly import generate_fly_toml

                self.write_file("fly.toml", generate_fly_toml(self.config))
            elif self.config.deployment == DeploymentTarget.CLOUDFLARE:
                from matt_stack.templates.deploy_cloudflare import generate_wrangler_toml

                self.write_file("wrangler.toml", generate_wrangler_toml(self.config))

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

    def _step_customize_frontend(self) -> bool:
        try:
            customize_frontend(self.config)
            return True
        except Exception as e:
            print_error(f"Failed to customize frontend: {e}")
            return False

    def _step_init_git(self) -> bool:
        return self.init_git_repository()
