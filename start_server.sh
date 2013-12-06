#!/bin/bash
cd src
gunicorn -c config_local.py sciwms.wsgi:application &
