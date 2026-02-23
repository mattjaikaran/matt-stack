# matt-stack

CLI tool to scaffold fullstack monorepos from battle-tested boilerplates.

## Tech Stack
- Python 3.12+, built with Typer + Rich + Questionary
- Package manager: `uv` (never pip/poetry)
- Build: hatchling

## Project Structure
- `src/matt_stack/` — main package
  - `cli.py` — Typer app entry point
  - `config.py` — enums, ProjectConfig dataclass, REPO_URLS
  - `presets.py` — preset definitions
  - `commands/` — init, doctor, info
  - `generators/` — BaseGenerator + fullstack/backend/frontend/ios
  - `post_processors/` — b2b, customizer, frontend_config
  - `templates/` — f-string template functions (no Jinja2)
  - `utils/` — console, git, docker, process helpers

## Key Patterns
- Templates are Python functions returning strings (f-strings, not Jinja2)
- All generators inherit from BaseGenerator
- ProjectConfig is the single config object passed everywhere
- `questionary` for interactive prompts, `rich` for output

## Commands
```bash
uv sync                    # Install deps
uv run matt-stack init     # Interactive wizard
uv run matt-stack doctor   # Check environment
uv run matt-stack info     # Show presets/repos
uv run pytest              # Run tests
```

## Code Style
- ruff for linting/formatting
- Type hints always
- Line length: 100
