#!/bin/bash

set -e

echo "Running database migration..."

cd /app/models/db_schemes/minirag/

alembic upgrade head

cd /app

exec "$@"
