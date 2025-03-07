#!/bin/sh
until cd /app
do
    echo "Waiting for server volume..."
done

celery -A erp_system worker --loglevel=info --concurrency 4 -E
