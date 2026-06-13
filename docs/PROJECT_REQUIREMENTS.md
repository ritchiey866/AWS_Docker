# Project Requirements

## Overview

Build a containerized Python web application that hosts a Flask app with PostgreSQL, supports development and production workflows, and provides admin-style management features through a browser UI.

## Functional requirements

### FR-1 Web application
- Host a Flask web application using Blueprint-based routing and Jinja2 HTML templates
- Serve static assets (CSS, JS)
- Provide a health check endpoint at `/health`

### FR-2 Database
- Run PostgreSQL in a separate Docker container (not baked into the app image)
- Persist database data in an updatable Docker volume that survives container restarts and rebuilds
- Apply schema changes via Flask-Migrate (Alembic) on container startup

### FR-3 Docker deployment
- Use **multi-container Docker Compose** (recommended architecture)
- Separate services: application, database, reverse proxy
- Support both **production** and **development** compose configurations
- Production: Gunicorn + Nginx
- Development: Flask debug server with code hot reload and optional direct DB access

### FR-4 Sample application data (Items CRUD)
- Provide a sample `items` entity with full CRUD in the UI
- Fields: name, description, created/updated timestamps

### FR-5 Authentication
- Login page as the application entry point (`/`)
- Validate credentials against a `users` table in PostgreSQL
- Store passwords hashed (not plain text)
- Seed a default admin account on first startup
- Protect authenticated routes; redirect unauthenticated users to login
- Logout support

### FR-6 Database management UI
- List all PostgreSQL tables with row counts and primary keys
- Create new tables via the UI (column name, type, PK, nullable)
- Browse table data with pagination
- Create, read, update, and delete rows in any table
- Drop non-system tables (protect migration metadata table)

### FR-7 Navigation & UX
- Left sidebar navigation on authenticated pages
- Multi-level expandable/collapsible menus
- Menu sections: Dashboard, Items, Database, Logout
- Collapsible sidebar pane
- Modern responsive UI using Tailwind CSS

## Non-functional requirements

### NFR-1 Portability
- Runs on Docker Desktop (Windows tested)
- Environment configuration via `.env` file

### NFR-2 Security (baseline)
- Session-based authentication
- SQL identifier validation for dynamic DB admin operations
- Parameterized queries for row data
- Secrets via environment variables (not hardcoded in production)

### NFR-3 Maintainability
- App factory pattern
- Blueprint separation by feature (auth, home, items, db_admin)
- Service layer for database admin logic
- Reusable Jinja2 macros for UI components

### NFR-4 Reliability
- PostgreSQL health check before app startup
- Auto-restart policy on all compose services
- Idempotent admin user seeding

## Out of scope (current version)

- User registration / password reset
- Role-based access control (beyond login gate)
- HTTPS / TLS termination
- AWS/ECS/EKS deployment manifests
- Automated test suite
- Email or background job processing

## Default configuration

| Setting | Default |
|---------|---------|
| App URL (production) | http://localhost:8080 |
| App URL (dev direct) | http://localhost:8000 |
| DB host port (dev) | 5432 |
| DB name | appdb |
| DB user | appuser |
| Admin username | admin |
| Admin password | password |
