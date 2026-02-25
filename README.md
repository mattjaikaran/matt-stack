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
| `matt-stack add <component>` | Add frontend/backend/ios to existing project |
| `matt-stack upgrade` | Pull latest boilerplate changes into project |
| `matt-stack audit [path]` | Run static analysis on a generated project |
| `matt-stack doctor` | Check your development environment |
| `matt-stack info` | Show available presets and source repos |
| `matt-stack config [action]` | Manage user config (show/path/init) |
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

### `add` Options

| Flag | Description |
|------|-------------|
| `--path, -p` | Project path (default: current directory) |
| `--framework, -f` | Frontend framework: `react-vite`, `react-vite-starter` |
| `--dry-run` | Preview what would be added |

### `upgrade` Options

| Flag | Description |
|------|-------------|
| `--component, -c` | Upgrade specific component: `backend`, `frontend` |
| `--dry-run` | Preview changes without applying them |
| `--force` | Overwrite modified files (use with caution) |

### `audit` Options

| Flag | Description |
|------|-------------|
| `--type, -t` | Audit type(s): `types`, `quality`, `endpoints`, `tests`, `dependencies`, `vulnerabilities` |
| `--severity, -s` | Minimum severity: `error`, `warning`, `info` |
| `--live` | Enable live endpoint probing (GET only, safe) |
| `--base-url` | Base URL for live probing (default: `http://localhost:8000`) |
| `--no-todo` | Skip writing to `tasks/todo.md` |
| `--json` | Machine-readable JSON output |
| `--html` | Generate browsable HTML dashboard report |
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

### 5. `dependencies` — Version compatibility

- Parses `pyproject.toml` (regex-based) and `package.json` for dependency info
- Finds unpinned dependencies (no version constraint)
- Detects overly broad constraints (`>=` without upper bound)
- Warns about deprecated packages (`nose`, `mock`, `moment`, `tslint`, etc.)
- Catches duplicate dependencies across regular/dev
- Flags TypeScript version conflicts across manifests

### Custom Auditors (Plugin System)

Drop `.py` files into `matt-stack-plugins/` in your project root to add custom audit rules. Each file should export a class that inherits `BaseAuditor`:

```python
from matt_stack.auditors.base import AuditType, BaseAuditor, Severity

class MyCustomAuditor(BaseAuditor):
    audit_type = AuditType.QUALITY  # or any AuditType

    def run(self):
        # your custom checks here
        return self.findings
```

## Generated Project Structure

```
my-app/
├── backend/                          # Django Ninja API
├── frontend/                         # React + Vite + TanStack Router
├── ios/                              # Swift iOS client (optional, auto-renamed)
├── docker-compose.yml
├── docker-compose.prod.yml
├── docker-compose.override.yml.example  # Per-developer customization
├── .pre-commit-config.yaml           # ruff + prettier hooks
├── Makefile                          # All commands: setup, up, test, lint, format
├── .env.example
├── .gitignore
├── CLAUDE.md                         # AI assistant context
├── README.md
└── tasks/
    └── todo.md                       # Audit findings land here
```

## iOS Support

Include an iOS client with any fullstack project:

```bash
# During project creation
matt-stack init my-app --preset starter-fullstack --ios

# Add to an existing project
matt-stack add ios --path /path/to/project
```

The iOS client is cloned from [swift-ios-starter](https://github.com/mattjaikaran/swift-ios-starter) and auto-renamed from the default `MyApp` to match your project's display name. It targets SwiftUI with iOS 17+ and uses the MVVM pattern.

**Backend networking**: The generated iOS project includes an API client configured with a base URL constant. Update it to point at your backend (e.g. `http://localhost:8000` for local development).

**Audit limitation**: The `matt-stack audit` command does not yet scan `.swift` files. Type safety, quality, and test auditors currently cover Python and TypeScript only.

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
│   ├── add.py          # Add components to existing projects
│   ├── upgrade.py      # Pull latest boilerplate changes
│   ├── audit.py        # Audit orchestrator
│   ├── doctor.py       # Environment validation
│   └── info.py         # Preset display
├── generators/
│   ├── base.py         # BaseGenerator (clone, strip, write)
│   ├── fullstack.py    # 8-step fullstack generation
│   ├── backend_only.py # 6-step backend generation
│   ├── frontend_only.py# 5-step frontend generation
│   └── ios.py          # iOS helper (auto-renames MyApp references)
├── auditors/
│   ├── base.py         # AuditFinding, AuditConfig, BaseAuditor
│   ├── types.py        # Pydantic ↔ TS/Zod comparison
│   ├── quality.py      # TODOs, stubs, debug, credentials
│   ├── endpoints.py    # Route analysis + live probing
│   ├── tests.py        # Coverage gaps + feature mapping
│   ├── dependencies.py # pyproject.toml + package.json checks
│   ├── report.py       # Rich tables + todo.md writer
│   ├── html_report.py  # Standalone HTML dashboard export
│   └── plugins.py      # Custom auditor plugin loader
├── parsers/
│   ├── python_schemas.py    # Pydantic class parser
│   ├── typescript_types.py  # TS interface parser
│   ├── zod_schemas.py       # Zod z.object() parser
│   ├── django_routes.py     # Route decorator parser
│   ├── test_files.py        # pytest/vitest parser
│   └── dependencies.py      # pyproject.toml + package.json parser
├── post_processors/
│   ├── customizer.py   # Rename backend/frontend
│   ├── frontend_config.py # Monorepo .env + vite config
│   └── b2b.py          # B2B feature instructions
├── templates/           # f-string template functions (all conditional on feature flags)
│                        # makefile, docker_compose, env, readme, gitignore, claude_md
│                        # pre_commit_config, docker_compose_override
│                        # deploy_railway, deploy_render, deploy_vercel
└── utils/               # console, git, docker, process, yaml_config
```

## Ecosystem

matt-stack is extensible -- bring your own boilerplates, presets, and audit plugins.

- **Custom repos & presets**: `~/.matt-stack/config.yaml` -- see [Ecosystem Guide](docs/ecosystem.md)
- **Audit plugins**: Drop `.py` files in `matt-stack-plugins/` -- see [Plugin Guide](docs/plugin-guide.md)
- **Deployment targets**: 8 platforms supported -- see [Deployment Guide](docs/deployment-guide.md)

```bash
matt-stack config init   # Create user config template
matt-stack config show   # View current config
```

## Development

```bash
uv sync                        # Install dependencies
uv run pytest -x -q            # Run tests (364 tests)
uv run pytest --cov            # With coverage
uv run ruff check src/ tests/  # Lint
uv run ruff format src/ tests/ # Format
```

## License

MIT
