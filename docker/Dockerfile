# readstore/django/docker/Dockerfile

FROM python:3.12-slim-bullseye

# Use bash to support string substitution.
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV DEBIAN_FRONTEND=noninteractive

# Install git python3 pip
RUN apt-get update \
&& apt-get upgrade -y \
&& apt-get upgrade -y gcc libpq-dev git \
&& rm -rf /var/lib/apt/lists/*

# Specify user
ARG UID=1000
ARG GID=1000
ARG WORKDIR=/home/nonroot

RUN groupadd -g "${GID}" nonroot \
  && adduser --uid $UID --gid $GID --disabled-password --gecos "" nonroot
  
USER nonroot
WORKDIR $WORKDIR

COPY --chown=nonroot:nonroot requirements.txt requirements.txt
COPY --chown=nonroot:nonroot readstore_basic/readstore_server_config.yaml readstore_server_config.yaml
COPY --chown=nonroot:nonroot readstore_basic/__version__.py __version__.py
COPY --chown=nonroot:nonroot readstore_basic/readstore_server.py readstore_server.py

COPY --chown=nonroot:nonroot readstore_basic/backend backend
COPY --chown=nonroot:nonroot readstore_basic/frontend frontend

# Requirements for pipeline
RUN pip3 install --user -r requirements.txt

# # UID Must Be added to the docker group

# Pip packages are installed in .local/bin
ENV PATH="${WORKDIR}/.local/bin:${PATH}"

EXPOSE 8501
EXPOSE 8000