#!/bin/bash
cd src
gunicorn_django -c config_local.py pywms/settings.py  &
#python manage.py run_gunicorn -c config_public.py &
