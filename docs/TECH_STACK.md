# Tech Stack

## Architecture

```
Browser
   │
   ▼
Nginx (:8080)          ← reverse proxy, static files
   │
   ▼
Gunicorn / Flask (:8000)   ← WSGI app (production)
   │
   ▼
PostgreSQL (:5432)     ← persistent volume: postgres_data
```

Development mode can bypass Nginx and connect to Flask directly on port 8000.

## Backend

| Component | Technology | Version / notes |
|-----------|------------|-----------------|
| Language | Python | 3.12 (slim Docker image) |
| Web framework | Flask | 3.1.0 |
| ORM | Flask-SQLAlchemy | 3.1.1 |
| Migrations | Flask-Migrate (Alembic) | 4.1.0 |
| DB driver | psycopg2-binary | 2.9.10 |
| WSGI server | Gunicorn | 23.0.0 (production) |
| Password hashing | Werkzeug (via Flask) | built-in |
| Config | python-dotenv | 1.1.0 |

## Database

| Component | Technology | Notes |
|-----------|------------|-------|
| RDBMS | PostgreSQL | 16-alpine official image |
| Persistence | Docker named volume | `postgres_data` |
| Schema tool | Alembic | migrations in `migrations/versions/` |

### Tables (application-managed)

| Table | Purpose |
|-------|---------|
| `items` | Sample CRUD entity |
| `users` | Authentication |
| `alembic_version` | Migration tracking (system) |
| *(dynamic)* | Tables created via Database Manager UI |

## Frontend

| Component | Technology | Notes |
|-----------|------------|-------|
| Templates | Jinja2 | `app/templates/` |
| CSS | Tailwind CSS | CDN (Play CDN) |
| Font | Inter | Google Fonts |
| Navigation | HTML `<details>`/`<summary>` | Native expand/collapse |
| Sidebar collapse | Inline JavaScript | `localStorage` state |
| Components | Jinja2 macros | `app/templates/_macros.html` |

## Infrastructure & DevOps

| Component | Technology | Notes |
|-----------|------------|-------|
| Containerization | Docker | Multi-stage build |
| Orchestration | Docker Compose | v2 compose format |
| Reverse proxy | Nginx | 1.27-alpine |
| Static files | Nginx volume mount | `./app/static` |
| Entrypoint | Bash script | migrate → seed admin → start app |

## Docker services

| Service | Image / build | Role |
|---------|---------------|------|
| `web` | Built from `Dockerfile` | Flask application |
| `db` | `postgres:16-alpine` | PostgreSQL database |
| `nginx` | `nginx:1.27-alpine` | Reverse proxy |

## Project structure

```
AWS_Docker/
├── app/
│   ├── blueprints/       auth, home, items, db_admin
│   ├── models/           SQLAlchemy models (Item, User)
│   ├── services/         db_admin service layer
│   ├── templates/        Jinja2 HTML + sidebar + macros
│   ├── static/           CSS, JS
│   ├── factory.py        App factory
│   └── wsgi.py           Gunicorn entry point
├── migrations/           Alembic migrations
├── nginx/                Nginx config
├── scripts/              entrypoint.sh, seed_admin.py
├── docs/                 Project documentation
├── docker-compose.yml    Production stack
├── docker-compose.dev.yml Dev overrides
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Environment variables

See `.env.example` for full list. Key variables:

| Variable | Purpose |
|----------|---------|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Database credentials |
| `DATABASE_URL` | SQLAlchemy connection string (internal) |
| `SECRET_KEY` | Flask session signing |
| `APP_ENV` | `production` or `development` |
| `NGINX_PORT` | Host port for web access (default 8080) |

## Compose commands

```powershell
# Production
docker compose up --build -d

# Development (hot reload)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```
