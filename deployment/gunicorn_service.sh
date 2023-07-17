#!/bin/bash
USER=root
GROUP=admin
NUM_WORKERS=1
DJANGO_DIR=/home/backend/
DJANGO_SETTINGS_MODULE=project_main.settings
DJANGO_WSGI_MODULE=project_main.wsgi
HOST='0.0.0.0:8000'

cd $DJANGO_DIR
source venv/bin/activate

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

# Start your Django gunicorn

exec gunicorn --workers=$NUM_WORKERS ${DJANGO_WSGI_MODULE}:application -b=$HOST