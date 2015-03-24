'''
COPYRIGHT 2010 RPS ASA

This file is part of SCI-WMS.

    SCI-WMS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    SCI-WMS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with SCI-WMS.  If not, see <http://www.gnu.org/licenses/>.
'''

# Django settings for fvcom_compute project.
import os

WSGI_APPLICATION = "sciwms.wsgi.application"

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# LOCALDATASET is for testing purposes
# If LOCALDATASET is populated, the service will use the cached
# TOPOLOGY for schema/grid information and LOCALDATASETPATH for actual data extraction
LOCALDATASET     = False
#LOCALDATASETPATH = {
#    '30yr_gom3' : "/home/user/Data/FVCOM/gom3_197802.nc",
#}


# Where to store the Topology data?
TOPOLOGY_PATH = os.path.abspath(os.path.join(PROJECT_ROOT, "apps", "wms", "topology"))
if not os.path.exists(TOPOLOGY_PATH):
    os.makedirs(TOPOLOGY_PATH)

DEBUG = False
TEMPLATE_DEBUG = False

ADMINS = (
    #('Your Name', 'youremail@domain.com'),
)

#EMAIL_HOST = ''
#EMAIL_HOST_USER = ''
#EMAIL_PORT = ''
#EMAIL_HOST_PASSWORD = ''
#EMAIL_SUBJECT_PREFIX = '[SCIWMS MESSAGE]'

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "sci-wms.db"))  # Or path to database file if using sqlite3.
    }
}
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "static"))

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

COMMON_STATIC_FILES = os.path.abspath(os.path.join(PROJECT_ROOT, "static", "common"))

# Additional locations of static files
STATICFILES_DIRS = (
    COMMON_STATIC_FILES,
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'zicip#n3_j%h&6tkb_p#9p571--=0g)2!-8xpq%dw*)_7uo=dw'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    #'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'sciwms.urls'

TEMPLATE_DIRS = (
    os.path.abspath(os.path.join(os.path.dirname(__file__), "templates")),
)

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'sciwms.apps.wms',
    'sciwms.apps.wmsrest',
    'rest_framework'
]

REST_FRAMEWORK = {
                  'DEFAULT_PERMISSION_ACCESS': ('rest_framework.permissions.IsAdminUser',),
                  'PAGINATE_BY': 10
                  }
