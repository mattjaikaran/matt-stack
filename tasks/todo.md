# matt-stack TODO

## Phase 1: Foundation

- pyproject.toml, .gitignore, CLAUDE.md, Makefile, LICENSE
- config.py — enums, ProjectConfig, REPO_URLS
- presets.py — preset definitions
- utils/console.py — Rich helpers
- utils/git.py — clone, init, commit
- utils/docker.py — detection helpers
- utils/process.py — subprocess runner
- **init**.py, **main**.py

## Phase 2: Templates

- templates/root_makefile.py
- templates/docker_compose.py
- templates/docker_compose_prod.py
- templates/root_env.py
- templates/root_readme.py
- templates/root_gitignore.py
- templates/root_claude_md.py

## Phase 3: Generators

- generators/base.py
- generators/backend_only.py
- generators/frontend_only.py
- generators/fullstack.py
- generators/ios.py

## Phase 4: Post-Processors

- post_processors/customizer.py
- post_processors/frontend_config.py
- post_processors/b2b.py

## Phase 5: Commands + CLI

- commands/doctor.py
- commands/info.py
- commands/init.py
- cli.py
- utils/yaml_config.py

## Phase 6: Polish

- README.md
- Tests (22 passing)
- E2E verification (all 4 preset types)
- Lint clean (ruff)

## Phase 7: Audit Command

- parsers/ — 5 regex-based parser modules
- auditors/base.py — data model (AuditFinding, AuditConfig, BaseAuditor)
- auditors/quality.py — TODOs, stubs, debug, credentials
- auditors/types.py — Pydantic ↔ TS/Zod comparison
- auditors/endpoints.py — route analysis + live probing
- auditors/tests.py — coverage gaps + feature mapping
- auditors/report.py — Rich tables + idempotent todo.md writer
- commands/audit.py — orchestrator
- cli.py — audit command wired
- Tests (48 passing — 26 new)
- E2E: audit on starter-fullstack produces 476 findings across all 4 domains
- E2E: idempotent todo.md re-write verified
- E2E: JSON output validated
- README.md — full rewrite with audit docs
- CLAUDE.md — expanded with file map, patterns, workflows

## Phase 8: Codebase Improvements (completed)

- Fix STUB_RE duplicate regex, doctor exit code, _validate_clone return value
- Refactor generators to ABC base class with shared run() loop
- Add --severity/-s filter to audit command
- Make extract_block string-aware for TS/Zod parsing
- Document DeploymentTarget enum as partially implemented
- Add --quiet/-q flag for CI-friendly output
- Add 25 tests for post-processors, iOS, docker utils, yaml edge cases (227 total)

## Phase 9: Tier 1 — Game-Changers (completed)

- `matt-stack add` — expand existing projects in-place (add frontend/backend/ios)
- `matt-stack upgrade` — pull latest boilerplate changes into existing project
- Deployment target scaffolding (Railway, Render, Cloudflare, DigitalOcean configs)

## Phase 10: Tier 2 — High-Value Polish (completed)

- Conditional template cleanup — templates 100% conditional on feature flags
- Dependency/version compatibility auditor (pyproject.toml + package.json)
- Pre-commit hooks auto-setup (.pre-commit-config.yaml with ruff + prettier)

## Phase 11: Tier 3 — Differentiators (completed)

- Audit HTML dashboard export (`--html` flag, browsable report, inline CSS/JS)
- Plugin system for custom auditors (load from ./matt-stack-plugins/)
- docker-compose.override.yml template for per-developer customization
- iOS generator customization (rename MyApp references)
- YAML config mode E2E test (8 tests covering all config paths)

## Phase 12: Client Command & Agent DX (completed)

- `utils/package_manager.py` — detect PM from lockfiles, abstract bun/npm/yarn/pnpm
- `commands/client.py` — `matt-stack client add/remove/install/run/dev/build/exec/which`
- `commands/context.py` — dump project context as markdown/JSON for AI agents
- Wire `client` subcommand group + `context` command into `cli.py`
- `user_config.py` — support `package_manager` preference (bun/npm/yarn/pnpm)
- Tests: 51 new tests (package_manager util, client command, context command)

## Phase 13: Tooling & DX Enhancements (completed)

- `commands/dev.py` — unified `matt-stack dev` (docker + backend + frontend)
- `commands/test.py` — unified `matt-stack test` (pytest + vitest, parallel mode)
- `commands/lint.py` — unified `matt-stack lint` (ruff + eslint, --fix, --format-check)
- `commands/env.py` — `matt-stack env check/sync/show` (.env management)
- `commands/version.py` — version display + PyPI update check
- `commands/completions.py` — shell completion installer (bash/zsh/fish)
- README.md — document all new commands, client, context, --quiet, --html, vulnerabilities
- CLAUDE.md — updated file map and CLI reference
- Tests: 81 new tests (586 total)

---

## Phase 14: New Boilerplate Support

### Next.js (App Router) — DONE

- Create `nextjs-starter` repo (in progress externally)
- Add `FrontendFramework.NEXTJS` enum + `is_nextjs` property
- Add `nextjs` to `REPO_URLS`
- Add presets: `nextjs-fullstack` (Next.js + Django API), `nextjs-frontend` (standalone)
- Add Next.js to interactive wizard choices
- Create `parsers/nextjs_routes.py` — parse App Router routes (`page.tsx`, `route.ts`)
- Extend endpoint auditor for Next.js API routes
- Next.js-aware templates: Makefile, docker-compose, env, readme, claude_md
- Next.js monorepo post-processor (next.config.monorepo.ts, .env.local)
- Removed Vercel, added Cloudflare + DigitalOcean deploy targets
- Upgrade command detects Next.js frontend (via next.config markers)
- docker-compose.override template uses correct env var prefix
- Doctor command uses generic "Frontend dev server" label
- 45 new tests (454 total)

### C# / ASP.NET

- Create `aspnet-boilerplate` repo — .NET 8, minimal API or controllers, EF Core, Identity
- Add preset: `starter-aspnet-api`
- Add preset: `starter-aspnet-fullstack` (with React frontend)
- Create `parsers/csharp_schemas.py` — parse C# classes with `[Required]`, `[StringLength]`, property types
- Extend type auditor for C# ↔ TypeScript cross-language checks
- Add `ProjectType.ASPNET_BACKEND` or handle via `backend_repo_key` routing
- Add deploy support: Docker, Azure App Service, AWS ECS

### Kotlin Android

- Create `kotlin-android-starter` repo — Jetpack Compose, MVVM, Retrofit, Room
- Add preset: `starter-android` (add to fullstack like iOS)
- Create `parsers/kotlin_schemas.py` — parse data classes with `@Serializable` annotation
- Extend type auditor for Kotlin ↔ Python/TS cross-language checks
- Add `config.include_android` flag (mirrors `include_ios` pattern)
- Wire into generators (similar to iOS flow)
- CI template for Android builds (GitHub Actions)

### React Native

- Create `react-native-starter` repo — Expo, TypeScript, React Navigation
- Add preset: `starter-mobile` (add to fullstack like iOS)
- Reuse existing TS parser (React Native is TypeScript)
- Existing TS/Zod auditor applies — no new parser needed
- Add `config.include_mobile` flag
- Add deploy support: EAS Build (Expo)
- Wire into generators (similar to iOS flow)

### Svelte / SvelteKit

- Create `sveltekit-boilerplate` repo — SvelteKit, TypeScript, form actions, load functions
- Add preset: `starter-sveltekit-fullstack` (SvelteKit + Django API)
- Add preset: `starter-sveltekit` (SvelteKit standalone)
- Create `parsers/svelte_schemas.py` — extract TS from `<script lang="ts">` blocks, Zod schemas
- Extend auditor for SvelteKit routes (`+page.server.ts`, `+server.ts`)
- Add `FrontendFramework.SVELTEKIT` enum value
- Add deploy support: Cloudflare, Docker, DigitalOcean

### Vue / Nuxt

- Create `nuxt-boilerplate` repo — Nuxt 3, TypeScript, auto-imports, composables
- Add preset: `starter-nuxt-fullstack`, `starter-nuxt`
- Create `parsers/vue_schemas.py` — extract TS from `<script setup lang="ts">` blocks
- Extend auditor for Nuxt routes (`server/api/**/*.ts`)
- Add `FrontendFramework.NUXT` enum value
- Add deploy support: Cloudflare, Docker, DigitalOcean

### Cross-cutting concerns for all new boilerplates

- Each new boilerplate needs a generator class (inherit BaseGenerator)
- Each needs Makefile targets added to `root_makefile.py`
- Each needs docker-compose service definitions where applicable
- Each needs README template additions
- Each needs CLAUDE.md template additions
- Type auditor `TYPE_COMPATIBILITY` dict needs language pair entries
- `NAME_CONVERTERS` dict needs language pair entries
- Tests for each new parser, generator, and preset

