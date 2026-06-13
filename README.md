# Flask + PostgreSQL Docker App

Multi-container Flask application with PostgreSQL, Nginx reverse proxy, authentication, database manager, and Tailwind CSS UI.

## Documentation

| Document | Description |
|----------|-------------|
| [AWS Deployment](docs/AWS_DEPLOYMENT.md) | Step-by-step guide to run on Amazon EC2 / AWS |
| [Session Summary](docs/SESSION_SUMMARY.md) | What was built and decisions made |
| [Project Requirements](docs/PROJECT_REQUIREMENTS.md) | Functional and non-functional requirements |
| [Tech Stack](docs/TECH_STACK.md) | Architecture, libraries, and infrastructure |
| [Features & Functions](docs/FEATURES.md) | Routes, CRUD, navigation, and operations |

## Quick start

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)

```powershell
cd c:\AWS_Docker
copy .env.example .env
docker compose up --build -d
```

Open **http://localhost:8080** and sign in with `admin` / `password`.

## Architecture

```
Browser → Nginx (:8080) → Gunicorn/Flask (:8000) → PostgreSQL
                ↓
           /static/ served by Nginx
```

## Development mode

```powershell
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Flask dev server: **http://localhost:8000** (hot reload)  
PostgreSQL: **localhost:5432**

## Common commands

```powershell
docker compose logs -f web
docker compose down              # stop, keep DB data
docker compose down -v           # stop, wipe DB data
docker compose exec web flask db upgrade
docker compose exec web flask db migrate -m "describe change"
```

## Project layout

```
AWS_Docker/
├── app/                  Flask application
├── migrations/           Alembic migrations
├── nginx/                Reverse proxy config
├── scripts/              Entrypoint & seed scripts
├── docs/                 Project documentation
├── docker-compose.yml    Production stack
└── docker-compose.dev.yml
```
