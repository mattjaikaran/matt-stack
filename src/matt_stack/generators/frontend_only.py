"""Frontend-only project generator."""

from __future__ import annotations

from matt_stack.generators.base import BaseGenerator
from matt_stack.post_processors.customizer import customize_frontend
from matt_stack.templates.root_gitignore import generate_gitignore
from matt_stack.templates.root_makefile import generate_makefile
from matt_stack.templates.root_readme import generate_readme
from matt_stack.utils.console import create_progress


class FrontendOnlyGenerator(BaseGenerator):
    """Generate a frontend-only project (React Vite SPA)."""

    def run(self) -> bool:
        steps = [
            ("Creating project directory", self._step_create_dir),
            ("Cloning frontend", self._step_clone_frontend),
            ("Creating root files", self._step_create_root_files),
            ("Customizing frontend", self._step_customize_frontend),
            ("Initializing git", self._step_init_git),
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

    def _step_clone_frontend(self) -> bool:
        return self.clone_and_strip(self.config.frontend_repo_key, "frontend")

    def _step_create_root_files(self) -> None:
        self.write_file("Makefile", generate_makefile(self.config))
        self.write_file("README.md", generate_readme(self.config))
        self.write_file(".gitignore", generate_gitignore(self.config))

    def _step_customize_frontend(self) -> None:
        customize_frontend(self.config)

    def _step_init_git(self) -> None:
        self.init_git_repository()
