#!/bin/bash
cd src
gunicorn -c config_local.py pywms.wsgi:application &
