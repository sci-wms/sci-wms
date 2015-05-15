FROM debian:wheezy
MAINTAINER Dave Foster <dave@axiomdatascience.com>

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get -y update && apt-get install -y \
    bash \
    bzip2 \
    git \
    libcurl4-openssl-dev \
    libevent-dev \
    libfreetype6-dev \
    libgeos-dev \
    libhdf5-dev \
    libjpeg-dev \
    libnetcdf-dev \
    libpng-dev \
    libspatialindex-dev \
    pwgen \
    python2.7 \
    python2.7-dev \
    python-mpltoolkits.basemap \
    python-pip \
    python-sqlite \
    sqlite \
    wget

COPY requirements*.txt /tmp/

RUN pip install --upgrade distribute
RUN pip install git+git://github.com/pyugrid/pyugrid
RUN pip install -r /tmp/requirements.txt
RUN pip install -r /tmp/requirements-prod.txt

RUN mkdir -p /apps/sci-wms
COPY . /apps/sci-wms
WORKDIR /apps/sci-wms

ENV DJANGO_SETTINGS_MODULE sciwms.settings.prod

RUN python manage.py migrate
RUN python manage.py collectstatic --noinput

# handle admin user
RUN chmod +x docker/*.sh
RUN touch ./.firstrun

VOLUME ["/data"]
EXPOSE 7002
ENTRYPOINT ["docker/run.sh"]

