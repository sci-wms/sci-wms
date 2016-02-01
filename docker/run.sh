#!/bin/bash

echo "Sourcing profile..."
. /etc/profile

export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-sciwms.settings.prod}

echo "Migrating sci-wms..."
python manage.py migrate

echo "Collecting sci-wms static assets..."
python manage.py collectstatic --noinput -v 0

USER=${SCIWMS_USERNAME:-sciwmsuser}
PASS=${SCIWMS_PASSWORD:-$(pwgen -s -1 16)}
SCIWMS_WEB_WORKERS=${SCIWMS_WEB_WORKERS:-4}

cat << EOF | python manage.py shell >/dev/null 2>&1
from django.contrib.auth.models import User
u, _ = User.objects.get_or_create(username='$USER')
u.set_password('$PASS')
u.is_superuser = True
u.is_staff = True
u.save()
EOF

echo "========================================================================"
echo "sci-wms user:         \"$USER\""
echo "sci-wms password:     \"$PASS\""
echo "========================================================================"

echo "Starting sci-wms..."
gunicorn --access-logfile - \
         --error-logfile - \
         --max-requests 50 \
         --keep-alive 5 \
         --backlog 50 \
         --log-level warning \
         -t 300 \
         -b 0.0.0.0:7002 \
         -w $SCIWMS_WEB_WORKERS \
         -k gevent \
         -e DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE \
         -n sciwms \
         sciwms.wsgi:application
