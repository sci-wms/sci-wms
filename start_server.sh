#!/bin/bash
gunicorn -c gunicorn_config_prod.py sciwms.wsgi:application
