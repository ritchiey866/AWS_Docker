#!/bin/bash
set -e

echo "Running database migrations..."
flask db upgrade

echo "Seeding default admin user..."
python /app/scripts/seed_admin.py

echo "Starting application..."
exec "$@"
