# matt-stack

CLI to scaffold fullstack monorepos from battle-tested boilerplates, then audit them for quality.

## Install

```bash
uv sync
```

Or install globally:

```bash
uv tool install .
```

Both `matt-stack` and `ms` are available as entry points.

## Quick Start

```bash
# Interactive wizard — walks you through every option
matt-stack init

# One-liner with preset
matt-stack init my-app --preset starter-fullstack

# With iOS client
matt-stack init my-app --preset starter-fullstack --ios

# From a YAML config file
matt-stack init --config project.yaml

# Specify output directory
matt-stack init my-app --preset b2b-fullstack -o ~/projects
```

## Commands

| Command | Description |
|---------|-------------|
| `matt-stack init [name]` | Create a new project from boilerplates |
| `matt-stack audit [path]` | Run static analysis on a generated project |
| `matt-stack doctor` | Check your development environment |
| `matt-stack info` | Show available presets and source repos |
| `matt-stack version` | Show version |

### Global Options

| Flag | Description |
|------|-------------|
| `--verbose, -v` | Show detailed output for debugging |

### `init` Options

| Flag | Description |
|------|-------------|
| `--preset, -p` | Use a preset (e.g. `starter-fullstack`, `b2b-api`) |
| `--config, -c` | Path to YAML config file |
| `--ios` | Include iOS client |
| `--output, -o` | Output directory (default: current) |
| `--dry-run` | Preview what would be generated without writing files |

### `audit` Options

| Flag | Description |
|------|-------------|
| `--type, -t` | Audit type(s): `types`, `quality`, `endpoints`, `tests` |
| `--live` | Enable live endpoint probing (GET only, safe) |
| `--base-url` | Base URL for live probing (default: `http://localhost:8000`) |
| `--no-todo` | Skip writing to `tasks/todo.md` |
| `--json` | Machine-readable JSON output |
| `--fix` | Auto-remove debug statements (`print()`, `console.log()`) |

```bash
# All audits on current directory
matt-stack audit

# Specific project path
matt-stack audit /path/to/project

# Type safety only
matt-stack audit -t types

# Multiple audit types
matt-stack audit -t quality -t tests

# Live endpoint probing (server must be running)
matt-stack audit -t endpoints --live

# JSON for CI pipelines
matt-stack audit --json

# Auto-fix debug statements
matt-stack audit -t quality --fix
```

## Presets

| Preset | Type | Description |
|--------|------|-------------|
| `starter-fullstack` | fullstack | Django Ninja + React Vite (TanStack Router) |
| `b2b-fullstack` | fullstack | B2B variant with orgs, teams, RBAC |
| `starter-api` | backend-only | Django Ninja API |
| `b2b-api` | backend-only | B2B backend with orgs, teams, RBAC |
| `starter-frontend` | frontend-only | React Vite (TanStack Router) |
| `simple-frontend` | frontend-only | React Vite (React Router, simpler) |

## Audit Domains

### 1. `types` — Pydantic ↔ TS/Zod sync

Parses Pydantic schemas from the backend and TypeScript interfaces + Zod schemas from the frontend, then compares:

- **Field presence**: finds fields in Python missing from TS/Zod (snake_case → camelCase aware)
- **Type compatibility**: `str → string`, `int → number`, `bool → boolean`, etc.
- **Optionality**: `Optional[str]` vs `field?: string`
- **Constraint sync**: `Field(min_length=3)` vs `.min(3)`

### 2. `quality` — Code quality

Scans all `.py`, `.ts`, `.tsx`, `.js`, `.jsx` files for:

- TODO/FIXME/HACK/XXX comments
- Stub functions (`pass`, `...`, `raise NotImplementedError`)
- Mock/placeholder data (`mock_`, `fake_`, `lorem ipsum`, hardcoded `localhost`)
- Hardcoded credentials (`admin/admin`, `password123`, `test@test.com`)
- Debug statements (`print()`, `console.log()`, `breakpoint()`, `debugger`)

### 3. `endpoints` — Route verification

- **Static**: parses `@router.get()` / `@http_get()` decorators, finds duplicates, missing auth on write endpoints, stub handlers
- **Live** (`--live`): GET-probes discovered endpoints, reports 500s and 404s (safe, read-only, never sends POST/PUT/DELETE)

### 4. `tests` — Coverage gaps

- Parses pytest (`test_*.py`) and vitest (`*.test.ts`) files
- Maps tests to feature areas (auth, user, crud, org)
- Finds schemas with no corresponding tests
- Reports empty test files and naming issues
- Suggests user story groupings for sparse areas

## Generated Project Structure

```
my-app/
├── backend/          # Django Ninja API
├── frontend/         # React + Vite + TanStack Router
├── ios/              # Swift iOS client (optional)
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile          # All commands: setup, up, test, lint, format
├── .env.example
├── .gitignore
├── CLAUDE.md         # AI assistant context
├── README.md
└── tasks/
    └── todo.md       # Audit findings land here
```

## Source Repositories

| Key | Repository |
|-----|-----------|
| `django-ninja` | [django-ninja-boilerplate](https://github.com/mattjaikaran/django-ninja-boilerplate) |
| `react-vite` | [react-vite-boilerplate](https://github.com/mattjaikaran/react-vite-boilerplate) |
| `react-vite-starter` | [react-vite-starter](https://github.com/mattjaikaran/react-vite-starter) |
| `swift-ios` | [swift-ios-starter](https://github.com/mattjaikaran/swift-ios-starter) |

## Architecture

```
src/matt_stack/
├── cli.py              # Typer app — all commands
├── config.py           # Enums, ProjectConfig, REPO_URLS
├── presets.py           # 6 preset definitions
├── commands/
│   ├── init.py         # Interactive wizard + routing
│   ├── audit.py        # Audit orchestrator
│   ├── doctor.py       # Environment validation
│   └── info.py         # Preset display
├── generators/
│   ├── base.py         # BaseGenerator (clone, strip, write)
│   ├── fullstack.py    # 8-step fullstack generation
│   ├── backend_only.py # 6-step backend generation
│   ├── frontend_only.py# 5-step frontend generation
│   └── ios.py          # iOS helper
├── auditors/
│   ├── base.py         # AuditFinding, AuditConfig, BaseAuditor
│   ├── types.py        # Pydantic ↔ TS/Zod comparison
│   ├── quality.py      # TODOs, stubs, debug, credentials
│   ├── endpoints.py    # Route analysis + live probing
│   ├── tests.py        # Coverage gaps + feature mapping
│   └── report.py       # Rich tables + todo.md writer
├── parsers/
│   ├── python_schemas.py    # Pydantic class parser
│   ├── typescript_types.py  # TS interface parser
│   ├── zod_schemas.py       # Zod z.object() parser
│   ├── django_routes.py     # Route decorator parser
│   └── test_files.py        # pytest/vitest parser
├── post_processors/
│   ├── customizer.py   # Rename backend/frontend
│   ├── frontend_config.py # Monorepo .env + vite config
│   └── b2b.py          # B2B feature instructions
├── templates/           # f-string template functions
└── utils/               # console, git, docker, process
```

## Development

```bash
uv sync                        # Install dependencies
uv run pytest                  # Run tests (176+ tests)
uv run pytest --cov            # With coverage
uv run ruff check src/ tests/  # Lint
uv run ruff format src/ tests/ # Format
```

## License

MIT
