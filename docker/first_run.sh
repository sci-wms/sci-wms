#!/bin/bash
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

