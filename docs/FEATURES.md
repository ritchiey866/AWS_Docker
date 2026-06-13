# Features & Functions

## Authentication

| Feature | Route | Description |
|---------|-------|-------------|
| Login | `GET/POST /` | Username/password form; validates against `users` table |
| Logout | `POST /logout` | Clears session, redirects to login |
| Session protection | — | Unauthenticated users redirected from protected pages |

**Default account:** `admin` / `password` (seeded on startup if not present)

---

## Dashboard

| Feature | Route | Description |
|---------|-------|-------------|
| Dashboard | `GET /dashboard` | Landing page after login; links to Items and Database Manager |
| Health check | `GET /health` | JSON `{"status": "ok"}` (no auth required) |

---

## Items (sample CRUD)

Blueprint: `items` — prefix `/items`

| Feature | Route | Method | Description |
|---------|-------|--------|-------------|
| List items | `/items/` | GET | Table of all items |
| Create item | `/items/new` | GET, POST | Form to add name + description |
| View item | `/items/<id>` | GET | Item detail with timestamps |
| Edit item | `/items/<id>/edit` | GET, POST | Update name + description |
| Delete item | `/items/<id>/delete` | POST | Remove item (with confirmation) |

**Model fields:** `id`, `name`, `description`, `created_at`, `updated_at`

---

## Database Manager

Blueprint: `db_admin` — prefix `/db`

| Feature | Route | Method | Description |
|---------|-------|--------|-------------|
| List tables | `/db/` | GET | All tables, row counts, primary keys |
| Create table | `/db/tables/create` | GET, POST | Define table name + columns |
| Browse table | `/db/tables/<name>/` | GET | Paginated row view (50/page) |
| New row | `/db/tables/<name>/rows/new` | GET, POST | Insert row into any table |
| Edit row | `/db/tables/<name>/rows/edit?id=…` | GET, POST | Update row by primary key |
| Delete row | `/db/tables/<name>/rows/delete` | POST | Delete row by primary key |
| Drop table | `/db/tables/<name>/drop` | POST | Drop table (except `alembic_version`) |

### Supported column types (create table)

`integer`, `serial`, `text`, `varchar`, `boolean`, `timestamp`, `numeric`

### Safety rules

- Table/column names validated (lowercase alphanumeric + underscore)
- Row operations use parameterized SQL
- `alembic_version` cannot be dropped

---

## Navigation (sidebar)

Available on all authenticated pages.

| Section | Links |
|---------|-------|
| Dashboard | `/dashboard` |
| **Items** ▾ | All Items, New Item |
| **Database** ▾ | All Tables, Create Table |
| Logout | POST to `/logout` |

### Navigation behavior

- **Submenus:** Native HTML `<details>`/`<summary>` — click section title to expand/collapse
- **Sidebar collapse:** ◀ button hides sidebar; ▶ floating button restores it
- **State:** Sidebar collapsed state saved in `localStorage`
- **Auto-expand:** Items or Database section opens automatically when on a matching page

---

## Background / startup tasks

Executed by `scripts/entrypoint.sh` on every `web` container start:

1. `flask db upgrade` — apply Alembic migrations
2. `python /app/scripts/seed_admin.py` — create admin user if missing
3. Start Gunicorn (production) or Flask dev server (development)

---

## Docker operations

| Operation | Command |
|-----------|---------|
| Start (production) | `docker compose up --build -d` |
| Start (development) | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build` |
| View logs | `docker compose logs -f web` |
| Stop (keep data) | `docker compose down` |
| Stop + wipe DB | `docker compose down -v` |
| DB backup | `docker compose exec db pg_dump -U appuser appdb > backup.sql` |

---

## URL quick reference

| URL | Auth | Purpose |
|-----|------|---------|
| http://localhost:8080/ | No | Login |
| http://localhost:8080/dashboard | Yes | Dashboard |
| http://localhost:8080/items/ | Yes | Items list |
| http://localhost:8080/db/ | Yes | Database tables |
| http://localhost:8080/health | No | Health check |
