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
ENV MINICONDA_VERSION "py38_4.8.2"
ENV MINICONDA_HASH "5bbb193fd201ebe25f4aeb3c58ba83feced6a25982ef4afa86d5506c3656c142"
RUN curl -k -o /miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-$MINICONDA_VERSION-Linux-x86_64.sh && \
    echo "${MINICONDA_HASH} /miniconda.sh" > /miniconda.sh.sha256 && \
    sha256sum --check /miniconda.sh.sha256 && \
    /bin/bash /miniconda.sh -b -p /opt/conda && \
    rm /miniconda.sh && \
    /opt/conda/bin/conda clean -afy && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> /etc/profile && \
    echo "conda activate base" >> /etc/profile && \
    find /opt/conda/ -follow -type f -name '*.a' -delete && \
    find /opt/conda/ -follow -type f -name '*.js.map' -delete && \
    /opt/conda/bin/conda update -n base conda && \
    /opt/conda/bin/conda clean -afy

COPY environment-prod.yml /tmp/environment.yml
RUN /opt/conda/bin/conda config \
        --set always_yes yes \
        --set changeps1 no \
        --set show_channel_urls True \
        && \
    /opt/conda/bin/conda config \
        --add channels conda-forge \
        && \
    # Install requirements
    /opt/conda/bin/conda env update -n base --file /tmp/environment.yml && \
    # cleanup
    /opt/conda/bin/conda clean -afy

ENV PATH /opt/conda/bin:$PATH

# Add Tini
ENV TINI_VERSION v0.19.0
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
