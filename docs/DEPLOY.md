# Deploy — Pack and Load Docker Images

This guide explains how to **export** the application Docker images from one machine and **import** them on another Docker host, without rebuilding from source or pulling from a registry.

Use this when moving the app to:

- An air-gapped / offline server
- A customer site without Git access
- AWS EC2 or any Linux/Windows host with Docker installed

---

## What gets packaged

This project runs three containers:

| Service | Image | Built locally? |
|---------|-------|----------------|
| `web` | `aws_docker-web:latest` | **Yes** — Flask app (Dockerfile) |
| `db` | `postgres:16-alpine` | No — public image |
| `nginx` | `nginx:1.27-alpine` | No — public image |

The **custom app image** is `aws_docker-web`. You must save this one at minimum.

For fully offline targets (no internet), also save `postgres:16-alpine` and `nginx:1.27-alpine`.

You still need these **project files** on the target host (they are not inside the image tar):

```
AWS_Docker/
├── docker-compose.yml
├── .env                    ← create from .env.example
├── nginx/nginx.conf
└── app/static/             ← mounted by Nginx for static assets
```

---

## Part 1 — Pack images (source machine)

Run these commands in the project root (`AWS_Docker/`).

### Step 1: Build the app image

```powershell
docker compose build web
```

Verify the image exists:

```powershell
docker images aws_docker-web
```

Expected output includes `aws_docker-web` with tag `latest`.

### Step 2: (Optional) Tag with a version

```powershell
docker tag aws_docker-web:latest aws_docker-web:1.0.0
```

Use a version tag when you ship multiple releases over time.

### Step 3: Save the app image to a tar file

**PowerShell (Windows):**

```powershell
docker save aws_docker-web:latest -o aws_docker-web.tar
```

**Linux / macOS:**

```bash
docker save aws_docker-web:latest -o aws_docker-web.tar
```

### Step 4: (Optional) Compress for transfer

Smaller files are easier to copy over SCP, USB, or S3.

**PowerShell:**

```powershell
Compress-Archive -Path aws_docker-web.tar -DestinationPath aws_docker-web.tar.zip
```

**Linux / macOS:**

```bash
gzip -k aws_docker-web.tar
# Creates aws_docker-web.tar.gz
```

### Step 5: (Optional) Save the full stack for offline use

Pull public images first, then save all three into one archive:

```powershell
docker pull postgres:16-alpine
docker pull nginx:1.27-alpine

docker save `
  aws_docker-web:latest `
  postgres:16-alpine `
  nginx:1.27-alpine `
  -o aws_docker-stack.tar
```

---

## Part 2 — Transfer files to the target host

Copy the image archive **and** the project folder to the new machine.

### Minimum files to copy

| Item | Purpose |
|------|---------|
| `aws_docker-web.tar` (or `.tar.gz` / `.zip`) | App container image |
| `docker-compose.yml` | Orchestration |
| `.env.example` → `.env` | Secrets and ports |
| `nginx/nginx.conf` | Reverse proxy config |
| `app/static/` | Static CSS/JS served by Nginx |

### Example: SCP to a remote Linux server

```powershell
scp aws_docker-web.tar user@192.168.1.100:~/
scp -r docker-compose.yml nginx app/static .env.example user@192.168.1.100:~/AWS_Docker/
```

Or copy the entire project directory plus the tar file.

---

## Part 3 — Load and run (target machine)

### Step 1: Install Docker

The target host needs:

- Docker Engine
- Docker Compose v2 (`docker compose` command)

See [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) for EC2 Docker install steps (also works on any Linux VM).

### Step 2: Load the image

**If compressed (zip):**

```powershell
Expand-Archive aws_docker-web.tar.zip -DestinationPath .
```

**If gzip:**

```bash
gunzip aws_docker-web.tar.gz
```

**Load into Docker:**

```powershell
docker load -i aws_docker-web.tar
```

Expected output:

```
Loaded image: aws_docker-web:latest
```

Verify:

```powershell
docker images aws_docker-web
```

### Step 3: (Optional) Load full offline stack

```powershell
docker load -i aws_docker-stack.tar
```

This restores `aws_docker-web`, `postgres:16-alpine`, and `nginx:1.27-alpine`.

If you did **not** bundle Postgres/Nginx, the target will pull them automatically on first `docker compose up` (requires internet).

### Step 4: Configure environment

```powershell
cd AWS_Docker
copy .env.example .env   # Windows
# cp .env.example .env   # Linux
```

Edit `.env` and set production values:

```env
POSTGRES_USER=appuser
POSTGRES_PASSWORD=<strong-password>
POSTGRES_DB=appdb
SECRET_KEY=<long-random-secret>
APP_ENV=production
NGINX_PORT=8080
```

### Step 5: Start the stack

Use `--no-build` so Compose uses the loaded image instead of rebuilding:

```powershell
docker compose up -d --no-build
```

If public images are not yet present locally and you have internet:

```powershell
docker compose up -d --no-build
```

Docker will pull `postgres:16-alpine` and `nginx:1.27-alpine` automatically.

Check status:

```powershell
docker compose ps
docker compose logs -f web
```

### Step 6: Open the app

```
http://<target-host-ip>:8080/
```

Default login: `admin` / `password` — change immediately after first login.

Health check:

```powershell
curl http://localhost:8080/health
```

---

## Quick reference

### Pack (source)

```powershell
docker compose build web
docker save aws_docker-web:latest -o aws_docker-web.tar
```

### Load (target)

```powershell
docker load -i aws_docker-web.tar
docker compose up -d --no-build
```

---

## Updating a deployed environment

When you release a new version:

1. **Source:** rebuild and save a new tar (optionally with a new tag).
2. **Transfer** the new tar to the target host.
3. **Target:**

```powershell
docker compose down
docker load -i aws_docker-web.tar
docker compose up -d --no-build
```

Database data persists in the `postgres_data` Docker volume across image updates.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Loaded image` shows a different name | Retag after load: `docker tag <id-or-name> aws_docker-web:latest` |
| Compose tries to rebuild | Use `docker compose up -d --no-build` |
| `web` container not found | Run `docker load` again; confirm with `docker images` |
| Nginx serves broken static files | Ensure `app/static/` exists on the host at the path in `docker-compose.yml` |
| Database connection errors | Check `.env` credentials match `docker-compose.yml` |
| Port already in use | Change `NGINX_PORT` in `.env` (e.g. `8081`) |

---

## Alternative: push to a container registry

For teams with network access, a registry is often easier than tar files:

```powershell
# Tag for your registry
docker tag aws_docker-web:latest ghcr.io/your-org/aws_docker-web:1.0.0

# Push
docker push ghcr.io/your-org/aws_docker-web:1.0.0
```

On the target host, update `docker-compose.yml` to use `image: ghcr.io/your-org/aws_docker-web:1.0.0` instead of `build:`, then run `docker compose pull && docker compose up -d`.

---

## Related documentation

- [AWS Deployment](AWS_DEPLOYMENT.md) — deploy on Amazon EC2
- [Tech Stack](TECH_STACK.md) — architecture overview
- [README](../README.md) — local development quick start
