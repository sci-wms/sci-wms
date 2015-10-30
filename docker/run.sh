#!/bin/bash

# Initialize first run
if [[ -e ./.firstrun ]]; then

    USER=${SCIWMS_USERNAME:-sciwmsuser}
    EMAIL=${SCIWMS_EMAIL:-sciwmsuser@localhost}
    PASS=${SCIWMS_PASSWORD:-$(pwgen -s -1 16)}

    cat << EOF | python manage.py shell >/dev/null 2>&1
from django.contrib.auth.models import User
User.objects.create_superuser('$USER', '$EMAIL', '$PASS')
EOF

    echo "========================================================================"
    echo "sci-wms user:         \"$USER\""
    echo "sci-wms user email:   \"$EMAIL\""
    echo "sci-wms password:     \"$PASS\""
    echo "========================================================================"

    rm ./.firstrun
fi

echo "Sourcing profile..."
. /etc/profile

export DJANGO_SETTINGS_MODULE=sciwms.settings.prod

echo "Migrating sci-wms..."
python manage.py migrate

echo "Collecting sci-wms static assets..."
python manage.py collectstatic --noinput -v 0

echo "Starting sci-wms..."
gunicorn --access-logfile - \
         --error-logfile - \
         --max-requests 50 \
         --keep-alive 5 \
         --backlog 50 \
         --log-level warning \
         -t 300 \
         -b 0.0.0.0:7002 \
         -w 8 \
         -k tornado \
         -e DJANGO_SETTINGS_MODULE=sciwms.settings.prod \
         -n sciwms \
         sciwms.wsgi:application
