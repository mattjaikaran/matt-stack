# matt-stack TODO

## Phase 1: Foundation
- [x] pyproject.toml, .gitignore, CLAUDE.md, Makefile, LICENSE
- [x] config.py — enums, ProjectConfig, REPO_URLS
- [x] presets.py — preset definitions
- [x] utils/console.py — Rich helpers
- [x] utils/git.py — clone, init, commit
- [x] utils/docker.py — detection helpers
- [x] utils/process.py — subprocess runner
- [x] __init__.py, __main__.py

## Phase 2: Templates
- [x] templates/root_makefile.py
- [x] templates/docker_compose.py
- [x] templates/docker_compose_prod.py
- [x] templates/root_env.py
- [x] templates/root_readme.py
- [x] templates/root_gitignore.py
- [x] templates/root_claude_md.py

## Phase 3: Generators
- [x] generators/base.py
- [x] generators/backend_only.py
- [x] generators/frontend_only.py
- [x] generators/fullstack.py
- [x] generators/ios.py

## Phase 4: Post-Processors
- [x] post_processors/customizer.py
- [x] post_processors/frontend_config.py
- [x] post_processors/b2b.py

## Phase 5: Commands + CLI
- [x] commands/doctor.py
- [x] commands/info.py
- [x] commands/init.py
- [x] cli.py
- [x] utils/yaml_config.py

## Phase 6: Polish
- [x] README.md
- [x] Tests (22 passing)
- [x] E2E verification (all 4 preset types)
- [x] Lint clean (ruff)

## Phase 7: Audit Command
- [x] parsers/ — 5 regex-based parser modules
- [x] auditors/base.py — data model (AuditFinding, AuditConfig, BaseAuditor)
- [x] auditors/quality.py — TODOs, stubs, debug, credentials
- [x] auditors/types.py — Pydantic ↔ TS/Zod comparison
- [x] auditors/endpoints.py — route analysis + live probing
- [x] auditors/tests.py — coverage gaps + feature mapping
- [x] auditors/report.py — Rich tables + idempotent todo.md writer
- [x] commands/audit.py — orchestrator
- [x] cli.py — audit command wired
- [x] Tests (48 passing — 26 new)
- [x] E2E: audit on starter-fullstack produces 476 findings across all 4 domains
- [x] E2E: idempotent todo.md re-write verified
- [x] E2E: JSON output validated
- [x] README.md — full rewrite with audit docs
- [x] CLAUDE.md — expanded with file map, patterns, workflows

## Phase 8: Codebase Improvements (completed)
- [x] Fix STUB_RE duplicate regex, doctor exit code, _validate_clone return value
- [x] Refactor generators to ABC base class with shared run() loop
- [x] Add --severity/-s filter to audit command
- [x] Make extract_block string-aware for TS/Zod parsing
- [x] Document DeploymentTarget enum as partially implemented
- [x] Add --quiet/-q flag for CI-friendly output
- [x] Add 25 tests for post-processors, iOS, docker utils, yaml edge cases (227 total)

## Phase 9: Tier 1 — Game-Changers
- [ ] `matt-stack add` — expand existing projects in-place (add frontend/backend/ios)
- [ ] `matt-stack upgrade` — pull latest boilerplate changes into existing project
- [ ] Deployment target scaffolding (Railway, Render, Vercel configs)

## Phase 10: Tier 2 — High-Value Polish
- [ ] Conditional template cleanup — make all templates 100% conditional on feature flags
- [ ] Dependency/version compatibility auditor (pyproject.toml + package.json)
- [ ] Pre-commit hooks auto-setup (.pre-commit-config.yaml with ruff + prettier)

## Phase 11: Tier 3 — Differentiators
- [ ] Audit HTML dashboard export (browsable report, inline CSS/JS)
- [ ] Plugin system for custom auditors (load from ./matt-stack-plugins/)
- [ ] docker-compose.override.yml template for per-developer customization
- [ ] iOS generator customization (rename MyApp references)
- [ ] YAML config mode E2E test
