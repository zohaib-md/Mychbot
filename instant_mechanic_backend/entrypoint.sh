#!/bin/sh
set -e

# Apply migrations on every start so a fresh volume gets its schema.
python manage.py migrate --noinput

exec "$@"
