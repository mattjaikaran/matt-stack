# matt-stack Ecosystem Guide

matt-stack is designed to be extensible. You can bring your own boilerplate repos, define custom presets, and write audit plugins.

## Custom Boilerplate Repos

Override or add new source repositories in `~/.matt-stack/config.yaml`:

```yaml
repos:
  # Override the default Django boilerplate
  django-ninja: https://github.com/myorg/django-boilerplate.git

  # Add new repositories
  nextjs: https://github.com/myorg/nextjs-boilerplate.git
  fastapi: https://github.com/myorg/fastapi-starter.git
```

User repos are merged with built-in repos. User entries take precedence (override by key).

### Using Custom Repos in Presets

Reference your custom repo keys in preset definitions:

```yaml
presets:
  my-fullstack:
    description: "Our team's fullstack setup"
    project_type: fullstack
    variant: starter
    frontend_framework: react-vite
```

## Custom Presets

Define presets in `~/.matt-stack/config.yaml`:

```yaml
presets:
  my-api:
    description: "Internal API template"
    project_type: backend-only
    variant: starter
    use_celery: false

  my-fullstack:
    description: "Our standard fullstack"
    project_type: fullstack
    variant: b2b
    frontend_framework: react-vite
    include_ios: true
    use_celery: true
```

### Preset Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `description` | string | auto | Human-readable description |
| `project_type` | string | fullstack | `fullstack`, `backend-only`, `frontend-only` |
| `variant` | string | starter | `starter`, `b2b` |
| `frontend_framework` | string | react-vite | `react-vite`, `react-vite-starter` |
| `include_ios` | bool | false | Include iOS client |
| `use_celery` | bool | true | Include Celery background tasks |

## Default Settings

Set project defaults so you don't have to specify them every time:

```yaml
defaults:
  deployment: railway
  use_celery: true
  use_redis: true
  init_git: true
```

## Config Commands

```bash
matt-stack config show   # Display current config
matt-stack config path   # Print config file path
matt-stack config init   # Create template config
```

## Plugin System

See [Plugin Guide](plugin-guide.md) for writing custom audit plugins.
