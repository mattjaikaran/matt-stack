# matt-stack Deployment Guide

matt-stack generates deployment configs for multiple platforms. Specify the target during init:

```bash
matt-stack init my-app --preset starter-fullstack  # default: docker
```

Or in a YAML config file:

```yaml
name: my-app
type: fullstack
deployment: railway  # docker, railway, render, fly-io, aws, gcp, hetzner, self-hosted
```

## Deployment Targets

### Docker (default)

Generated files: `docker-compose.yml`, `docker-compose.prod.yml`, `docker-compose.override.yml.example`

Best for: Local development, any hosting with Docker support.

### Railway

Generated files: `railway.json`, `railway.toml`

Best for: Quick deployments with automatic scaling. Connects to GitHub for auto-deploy.

### Render

Generated files: `render.yaml`

Best for: Blueprint-based infrastructure-as-code. Supports web services, databases, workers.

### Fly.io

Generated files: `fly.toml`

Best for: Edge deployments close to users. Good for APIs that need low latency.

### AWS (ECS/Copilot)

Generated files: `ecs-task-definition.json`, `copilot/api/manifest.yml`

Best for: Production workloads needing full AWS ecosystem (RDS, ElastiCache, CloudWatch).

### GCP (Cloud Run / App Engine)

Generated files: `service.yaml` (Cloud Run), `app.yaml` (App Engine)

Best for: Google Cloud users. Cloud Run for containers, App Engine for managed platform.

### Hetzner

Generated files: `docker-compose.prod.yml` (with Caddy), `Caddyfile`

Best for: Cost-effective European hosting. Caddy provides automatic HTTPS.

### Self-Hosted (Ubuntu/VPS)

Generated files: `docker-compose.prod.yml` (with nginx), `nginx.conf`, `<project>.service`

Best for: Full control on any VPS. Includes nginx, certbot for SSL, systemd for process management.

## Post-Generation Steps

All deployment configs use placeholder values that need updating:

1. **Domain names**: Replace `*.example.com` with your actual domain
2. **Environment variables**: Configure `.env` with production values
3. **Database**: Set up production database credentials
4. **SSL**: Configure certificates (automatic with Caddy/certbot, manual for others)
5. **Docker images**: Build and push to your container registry
