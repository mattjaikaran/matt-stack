# matt-stack

CLI tool to scaffold fullstack monorepos and audit them for quality.

## Tech Stack
- Python 3.12+, Typer + Rich + Questionary + PyYAML
- Package manager: `uv` (never pip/poetry)
- Build: hatchling
- Linter: ruff (line-length=100, select E,F,I,N,UP,B,SIM)

## CLI Reference

```bash
matt-stack init [name]           # Create project (interactive or preset)
matt-stack init my-app -p starter-fullstack  # Preset mode
matt-stack init --config f.yaml  # Config file mode
matt-stack add frontend          # Add component to existing project
matt-stack add backend --path .  # Add backend to frontend-only project
matt-stack add ios               # Add iOS client
matt-stack upgrade               # Pull latest boilerplate changes
matt-stack upgrade -c backend    # Upgrade specific component
matt-stack upgrade --dry-run     # Preview changes without applying
matt-stack audit [path]          # Static analysis (all 5 domains)
matt-stack audit -t quality      # Single domain
matt-stack audit -t dependencies # Dependency version checks
matt-stack audit --json          # Machine-readable
matt-stack audit --html          # Browsable HTML dashboard
matt-stack audit --fix           # Auto-remove debug statements
matt-stack audit -s error        # Filter by minimum severity
matt-stack doctor                # Check environment
matt-stack info                  # Show presets and repos
```

## File Map

```
src/matt_stack/
├── cli.py              # Typer app — 8 commands: init, add, upgrade, audit (--html), doctor, info, presets, version
├── config.py           # ProjectType, Variant, FrontendFramework, DeploymentTarget enums
│                       # ProjectConfig dataclass (13 fields, 9 computed properties incl. is_nextjs)
│                       # REPO_URLS dict, normalize_name(), to_python_package()
├── presets.py          # 8 presets: starter-fullstack, b2b-fullstack, starter-api, b2b-api,
│                       #            starter-frontend, simple-frontend, nextjs-fullstack, nextjs-frontend
│
├── commands/
│   ├── init.py         # run_init() — 3 modes: config-file → preset → interactive wizard
│   ├── add.py          # run_add() — add frontend/backend/ios to existing project
│   ├── upgrade.py      # run_upgrade() — pull latest boilerplate changes, diff + apply
│   ├── audit.py        # run_audit() — orchestrates 5 auditor classes + plugins, writes report
│   ├── doctor.py       # run_doctor() — checks python, git, uv, bun, make, docker, ports
│   └── info.py         # run_info() — 3 tables: presets, repos, examples
│
├── generators/
│   ├── base.py         # BaseGenerator: create_root_directory, clone_and_strip, write_file,
│   │                   #   update_file, update_file_regex, update_json_file, init_git_repository
│   ├── fullstack.py    # FullstackGenerator: 8 steps (9 with iOS)
│   ├── backend_only.py # BackendOnlyGenerator: 6 steps
│   ├── frontend_only.py# FrontendOnlyGenerator: 5 steps
│   └── ios.py          # add_ios_to_project() + MyApp rename customization
│
├── auditors/
│   ├── base.py         # Severity (error/warning/info), AuditType (types/quality/endpoints/tests/dependencies)
│   │                   # AuditFinding, AuditConfig, BaseAuditor, AuditReport
│   ├── types.py        # TypeSafetyAuditor — Pydantic ↔ TS interface/Zod field comparison
│   ├── quality.py      # CodeQualityAuditor — TODOs, stubs, mock data, debug, credentials
│   ├── endpoints.py    # EndpointAuditor — duplicate routes, missing auth, stubs, live probing
│   ├── tests.py        # CoverageAuditor — coverage gaps, naming, feature mapping
│   ├── dependencies.py # DependencyAuditor — unpinned, deprecated, duplicates, version conflicts
│   ├── report.py       # print_report() (Rich table), print_json(), write_todo() (idempotent)
│   ├── html_report.py  # generate_html_report() — standalone HTML dashboard with inline CSS/JS
│   └── plugins.py      # discover_plugins() — loads BaseAuditor subclasses from matt-stack-plugins/
│
├── parsers/
│   ├── python_schemas.py    # PydanticSchema/PydanticField, parse_pydantic_file(), find_schema_files()
│   ├── typescript_types.py  # TSInterface/TSField, parse_typescript_file(), find_typescript_type_files()
│   ├── zod_schemas.py       # ZodSchema/ZodField, parse_zod_file(), find_zod_files()
│   ├── django_routes.py     # Route, parse_routes_file(), find_route_files()
│   ├── nextjs_routes.py     # NextjsRoute, parse_nextjs_routes(), find_nextjs_app_dirs()
│   ├── test_files.py        # TestCase/TestSuite, parse_pytest_file(), parse_vitest_file()
│   └── dependencies.py      # Dependency/DependencyManifest, parse_pyproject_toml(), parse_package_json()
│
├── post_processors/    # customizer (rename), frontend_config (monorepo), b2b (instructions)
├── templates/          # f-string functions (all conditional on feature flags):
│                       # makefile, docker_compose, env, readme, gitignore, claude_md
│                       # pre_commit_config, docker_compose_override
│                       # deploy_railway, deploy_render, deploy_cloudflare, deploy_digitalocean
└── utils/              # console (Rich helpers), git, docker, process, yaml_config
```

## Key Patterns

1. **Templates = Python functions** returning f-strings (not Jinja2). All in `templates/`.
2. **Generators inherit BaseGenerator (ABC)**. Each defines a `steps` property; base class runs them.
3. **ProjectConfig** is the single config object passed everywhere. Computed properties: `has_backend`, `has_frontend`, `is_fullstack`, `is_b2b`, `is_nextjs`, `backend_dir`, `frontend_dir`.
4. **Parsers are pure functions** — regex-based, no AST, no new dependencies. Each returns dataclasses.
5. **Auditors inherit BaseAuditor**. Each has `run() → list[AuditFinding]`, uses `self.add_finding()`.
6. **Plugins** — custom auditors in `matt-stack-plugins/` are auto-discovered via `importlib.util`.
7. **Report writer** uses `<!-- audit:start -->` / `<!-- audit:end -->` markers for idempotent todo.md updates.
8. **HTML report** — `--html` generates standalone dashboard with inline CSS/JS, filter buttons, severity badges.
9. **Lazy imports** in `cli.py` — each command imports its module only when invoked.

## Common Workflows

### Add a new audit domain
1. Create `parsers/new_parser.py` with parse function + find function
2. Create `auditors/new_auditor.py` inheriting `BaseAuditor`
3. Add to `AUDITOR_CLASSES` dict in `commands/audit.py`
4. Add to `AuditType` enum in `auditors/base.py`

### Add a new preset
1. Add to `PRESETS` list in `presets.py`
2. No other changes needed — init command auto-discovers presets

### Add a new generator
1. Create `generators/new_type.py` inheriting `BaseGenerator`
2. Implement `steps` property returning `list[tuple[str, Callable]]`
3. Add routing in `commands/init.py`

### Add a new template
1. Create function in `templates/new_template.py`
2. Call from the appropriate generator

## Dev Commands

```bash
uv sync                        # Install
uv run pytest -x -q            # Tests (505 tests)
uv run ruff check src/ tests/  # Lint
uv run ruff format src/ tests/ # Format
uv run matt-stack init test --preset starter-fullstack -o /tmp  # E2E test
uv run matt-stack audit /tmp/test  # E2E audit test
```

## Rules
- `uv` only (never pip/poetry)
- `bun` for JS (never npm/yarn)
- Type hints on every function
- No new dependencies — stdlib + typer/rich/questionary/pyyaml only
- Parsers use regex, not AST libs
- All auditors must produce `AuditFinding` objects
- Tests go in `tests/` mirroring `src/` structure
