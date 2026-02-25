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

## Phase 9: Tier 1 — Game-Changers (completed)
- [x] `matt-stack add` — expand existing projects in-place (add frontend/backend/ios)
- [x] `matt-stack upgrade` — pull latest boilerplate changes into existing project
- [x] Deployment target scaffolding (Railway, Render, Vercel configs)

## Phase 10: Tier 2 — High-Value Polish (completed)
- [x] Conditional template cleanup — templates 100% conditional on feature flags
- [x] Dependency/version compatibility auditor (pyproject.toml + package.json)
- [x] Pre-commit hooks auto-setup (.pre-commit-config.yaml with ruff + prettier)

## Phase 11: Tier 3 — Differentiators (completed)
- [x] Audit HTML dashboard export (`--html` flag, browsable report, inline CSS/JS)
- [x] Plugin system for custom auditors (load from ./matt-stack-plugins/)
- [x] docker-compose.override.yml template for per-developer customization
- [x] iOS generator customization (rename MyApp references)
- [x] YAML config mode E2E test (8 tests covering all config paths)

---

## Phase 14: New Boilerplate Support (Future)

### Next.js (App Router)
- [ ] Create `nextjs-app-boilerplate` repo — App Router, TypeScript, Tailwind, server actions, middleware auth
- [ ] Add preset: `starter-nextjs-fullstack` (Next.js + Django API)
- [ ] Add preset: `starter-nextjs` (Next.js standalone)
- [ ] Create `parsers/nextjs_routes.py` — parse app directory route segments (`app/**/page.tsx`, `app/api/**/route.ts`)
- [ ] Extend endpoint auditor for Next.js API routes (`app/api/*/route.ts`)
- [ ] Add deploy support: Vercel (native), Docker (standalone output)
- [ ] Add `FrontendFramework.NEXTJS` enum value
- [ ] Wire into generators (new `NextjsFullstackGenerator` or extend existing)

### C# / ASP.NET
- [ ] Create `aspnet-boilerplate` repo — .NET 8, minimal API or controllers, EF Core, Identity
- [ ] Add preset: `starter-aspnet-api`
- [ ] Add preset: `starter-aspnet-fullstack` (with React frontend)
- [ ] Create `parsers/csharp_schemas.py` — parse C# classes with `[Required]`, `[StringLength]`, property types
- [ ] Extend type auditor for C# ↔ TypeScript cross-language checks
- [ ] Add `ProjectType.ASPNET_BACKEND` or handle via `backend_repo_key` routing
- [ ] Add deploy support: Docker, Azure App Service, AWS ECS

### Kotlin Android
- [ ] Create `kotlin-android-starter` repo — Jetpack Compose, MVVM, Retrofit, Room
- [ ] Add preset: `starter-android` (add to fullstack like iOS)
- [ ] Create `parsers/kotlin_schemas.py` — parse data classes with `@Serializable` annotation
- [ ] Extend type auditor for Kotlin ↔ Python/TS cross-language checks
- [ ] Add `config.include_android` flag (mirrors `include_ios` pattern)
- [ ] Wire into generators (similar to iOS flow)
- [ ] CI template for Android builds (GitHub Actions)

### React Native
- [ ] Create `react-native-starter` repo — Expo, TypeScript, React Navigation
- [ ] Add preset: `starter-mobile` (add to fullstack like iOS)
- [ ] Reuse existing TS parser (React Native is TypeScript)
- [ ] Existing TS/Zod auditor applies — no new parser needed
- [ ] Add `config.include_mobile` flag
- [ ] Add deploy support: EAS Build (Expo)
- [ ] Wire into generators (similar to iOS flow)

### Svelte / SvelteKit
- [ ] Create `sveltekit-boilerplate` repo — SvelteKit, TypeScript, form actions, load functions
- [ ] Add preset: `starter-sveltekit-fullstack` (SvelteKit + Django API)
- [ ] Add preset: `starter-sveltekit` (SvelteKit standalone)
- [ ] Create `parsers/svelte_schemas.py` — extract TS from `<script lang="ts">` blocks, Zod schemas
- [ ] Extend auditor for SvelteKit routes (`+page.server.ts`, `+server.ts`)
- [ ] Add `FrontendFramework.SVELTEKIT` enum value
- [ ] Add deploy support: Vercel, Node adapter, Docker

### Vue / Nuxt
- [ ] Create `nuxt-boilerplate` repo — Nuxt 3, TypeScript, auto-imports, composables
- [ ] Add preset: `starter-nuxt-fullstack`, `starter-nuxt`
- [ ] Create `parsers/vue_schemas.py` — extract TS from `<script setup lang="ts">` blocks
- [ ] Extend auditor for Nuxt routes (`server/api/**/*.ts`)
- [ ] Add `FrontendFramework.NUXT` enum value
- [ ] Add deploy support: Vercel, Nitro, Docker

### Cross-cutting concerns for all new boilerplates
- [ ] Each new boilerplate needs a generator class (inherit BaseGenerator)
- [ ] Each needs Makefile targets added to `root_makefile.py`
- [ ] Each needs docker-compose service definitions where applicable
- [ ] Each needs README template additions
- [ ] Each needs CLAUDE.md template additions
- [ ] Type auditor `TYPE_COMPATIBILITY` dict needs language pair entries
- [ ] `NAME_CONVERTERS` dict needs language pair entries
- [ ] Tests for each new parser, generator, and preset
