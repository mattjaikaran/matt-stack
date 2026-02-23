"""Backend-only project generator."""

from __future__ import annotations

from matt_stack.generators.base import BaseGenerator
from matt_stack.post_processors.b2b import print_b2b_instructions
from matt_stack.post_processors.customizer import customize_backend
from matt_stack.templates.docker_compose import generate_docker_compose
from matt_stack.templates.docker_compose_prod import generate_docker_compose_prod
from matt_stack.templates.root_claude_md import generate_claude_md
from matt_stack.templates.root_env import generate_env_example
from matt_stack.templates.root_gitignore import generate_gitignore
from matt_stack.templates.root_makefile import generate_makefile
from matt_stack.templates.root_readme import generate_readme
from matt_stack.utils.console import create_progress


class BackendOnlyGenerator(BaseGenerator):
    """Generate a backend-only project (Django API)."""

    def run(self) -> bool:
        steps = [
            ("Creating project directory", self._step_create_dir),
            ("Cloning backend", self._step_clone_backend),
            ("Creating root files", self._step_create_root_files),
            ("Customizing backend", self._step_customize_backend),
            ("Initializing git", self._step_init_git),
            ("Finishing up", self._step_finish),
        ]

        with create_progress() as progress:
            task = progress.add_task("Generating project...", total=len(steps))
            for description, step_fn in steps:
                progress.update(task, description=description)
                result = step_fn()
                if result is False:
                    return False
                progress.advance(task)

        return True

    def _step_create_dir(self) -> bool:
        return self.create_root_directory()

    def _step_clone_backend(self) -> bool:
        return self.clone_and_strip(self.config.backend_repo_key, "backend")

    def _step_create_root_files(self) -> None:
        self.write_file("Makefile", generate_makefile(self.config))
        self.write_file("docker-compose.yml", generate_docker_compose(self.config))
        self.write_file("docker-compose.prod.yml", generate_docker_compose_prod(self.config))
        self.write_file(".env.example", generate_env_example(self.config))
        self.write_file(".env", generate_env_example(self.config))
        self.write_file("README.md", generate_readme(self.config))
        self.write_file("CLAUDE.md", generate_claude_md(self.config))
        self.write_file(".gitignore", generate_gitignore(self.config))
        self.write_file("tasks/todo.md", f"# {self.config.display_name} TODO\n")

    def _step_customize_backend(self) -> None:
        customize_backend(self.config)

    def _step_init_git(self) -> None:
        self.init_git_repository()

    def _step_finish(self) -> None:
        if self.config.is_b2b:
            print_b2b_instructions(self.config)
