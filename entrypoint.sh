#!/bin/sh
set -e

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi
python manage.py migrate
python manage.py collectstatic --no-input

# Function to start Gunicorn with dynamic reload-extra-file options
start_gunicorn() {
    # Generate the reload-extra-file options dynamically
    extra_files=$(find /home/app/web -name "*.py" -printf "--reload-extra-file %p ")

    # Start Gunicorn
    echo "Starting Gunicorn..."
    gunicorn --config gunicorn-cfg.py --reload --reload-engine=poll $extra_files yourwakeel.wsgi
}

# Start Gunicorn
start_gunicorn

exec "$@"