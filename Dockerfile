FROM debian:stretch

LABEL maintainer="Kyle Wilcox <kyle@axiomdatascience.com>" \
      description='sci-wms is an open-source Python implementation of a WMS \
(Web Mapping Service) server designed for oceanographic, atmospheric, climate \
and weather data'

ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8

RUN apt-get update && apt-get install -y \
        binutils \
        build-essential \
        bzip2 \
        ca-certificates \
        curl \
        file \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        pwgen \
        wget \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Setup CONDA (https://hub.docker.com/r/continuumio/miniconda3/~/dockerfile/)
ENV MINICONDA_VERSION latest
RUN echo 'export PATH=/opt/conda/bin:$PATH' > /etc/profile.d/conda.sh && \
    curl -k -o /miniconda.sh https://repo.continuum.io/miniconda/Miniconda3-$MINICONDA_VERSION-Linux-x86_64.sh && \
    /bin/bash /miniconda.sh -b -p /opt/conda && \
    rm /miniconda.sh && \
    /opt/conda/bin/conda config \
        --set always_yes yes \
        --set changeps1 no \
        --set show_channel_urls True \
        && \
    /opt/conda/bin/conda config \
        --add channels axiom-data-science \
        --add channels conda-forge \
        && \
    /opt/conda/bin/conda clean -a -y

ENV PATH /opt/conda/bin:$PATH

# Copy over environment definition
COPY environment-prod.yml /tmp/environment.yml
RUN conda env update -n root --file /tmp/environment.yml && \
    conda clean -a -y

# Add Tini
ENV TINI_VERSION v0.18.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini
ENTRYPOINT ["/tini", "--"]

ENV SCIWMS_ROOT /srv/sci-wms
RUN mkdir -p "$SCIWMS_ROOT"
COPY . $SCIWMS_ROOT
WORKDIR $SCIWMS_ROOT

VOLUME ["$SCIWMS_ROOT/sciwms/settings/local"]
VOLUME ["$SCIWMS_ROOT/wms/topology"]
VOLUME ["$SCIWMS_ROOT/sciwms/db"]

EXPOSE 7002
CMD ["docker/run.sh"]
