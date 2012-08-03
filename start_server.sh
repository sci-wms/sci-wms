#!/bin/bash
cd src/pywms/
gunicorn_django -c config_public.py &
