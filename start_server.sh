#!/bin/bash
cd src/pywms/
gunicorn_django -c config_public.py &
#python manage.py run_gunicorn -c config_public.py &
