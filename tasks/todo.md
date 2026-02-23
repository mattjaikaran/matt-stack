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

## Future
- [ ] `matt-stack audit` command — type safety audit (Pydantic ↔ Zod/TS sync)
- [ ] Auto-append audit results to generated tasks/todo.md
- [ ] YAML config mode E2E test
- [ ] iOS generator customization (rename MyApp references)
