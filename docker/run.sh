#!/bin/bash

# Initialize first run
if [[ -e ./.firstrun ]]; then
    ./docker/first_run.sh
fi

echo "Starting sci-wms..."
gunicorn -c docker/gunicorn_config.py sciwms.wsgi:application
