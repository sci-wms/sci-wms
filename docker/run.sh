#!/bin/bash

echo "Sourcing profile..."
. /etc/profile
conda activate base

export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-sciwms.settings.quick}

echo "Migrating sci-wms..."
python manage.py migrate

echo "Collecting sci-wms static assets..."
python manage.py collectstatic --noinput -v 0

USER=${SCIWMS_USERNAME:-sciwmsuser}
PASS=${SCIWMS_PASSWORD:-$(pwgen -s -1 16)}

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
gunicorn -c docker/gunicorn.py sciwms.wsgi:application
