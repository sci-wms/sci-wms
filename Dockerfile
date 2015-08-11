FROM debian:jessie

MAINTAINER Dave Foster <dave@axiomdatascience.com>

# Setup CONDA (https://hub.docker.com/r/continuumio/miniconda3/~/dockerfile/)
RUN apt-get update && apt-get install -y wget bzip2 ca-certificates pwgen \
    libglib2.0-0 libxext6 libsm6 libxrender1
RUN echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    wget --quiet https://repo.continuum.io/miniconda/Miniconda-3.10.1-Linux-x86_64.sh && \
    /bin/bash /Miniconda-3.10.1-Linux-x86_64.sh -b -p /opt/conda && \
    rm Miniconda-3.10.1-Linux-x86_64.sh && \
    /opt/conda/bin/conda install --yes conda==3.14.1

ENV PATH /opt/conda/bin:$PATH
ENV DEBIAN_FRONTEND noninteractive

# Install requirements
COPY requirements*.txt /tmp/
RUN pip install django-extensions
RUN conda install --channel ioos --file /tmp/requirements.txt
RUN conda install --channel ioos --file /tmp/requirements-prod.txt

RUN mkdir -p /srv/sci-wms
COPY . /srv/sci-wms
RUN rm -f /srv/sci-wms/sciwms/sci-wms.db
WORKDIR /srv/sci-wms

ENV DJANGO_SETTINGS_MODULE sciwms.settings.prod

RUN python manage.py migrate --noinput
RUN python manage.py collectstatic --noinput

# handle admin user
RUN chmod +x docker/*.sh
RUN touch ./.firstrun

VOLUME ["/data"]
EXPOSE 7002
ENTRYPOINT ["docker/run.sh"]

