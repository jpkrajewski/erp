#!/bin/sh
set -e  # Exit immediately if a command exits with a non-zero status.
set -x  # Print each command before executing

echo "Running Migrations..."
python3 manage.py migrate --noinput

echo "Collecting Static Files..."
python3 manage.py collectstatic --noinput

echo "Running Populate Script..."
python3 manage.py populate

python3 manage.py runserver 0.0.0.0:8000
# Execute CMD from Dockerfile
exec "$@"
