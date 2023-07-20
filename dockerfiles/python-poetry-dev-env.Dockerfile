# podman build -t python-dev-env -f dockerfiles/python-poetry-dev-env.Dockerfile --build-arg=PYTHON_IMAGE=python:3.11-bookworm
ARG PYTHON_IMAGE=python:3.11-bookworm
FROM $PYTHON_IMAGE AS base
# Create our unprivileged user
RUN useradd -m -s /bin/bash --uid 1000 py --no-log-init
RUN mkdir -p /py && chown -R py:py /py
USER py
WORKDIR /py
RUN python3 -m pip install --user pipx
RUN python3 -m pipx ensurepath
ENV PATH=/home/py/.local/bin:$PATH
RUN pipx install poetry
RUN poetry config virtualenvs.in-project true

FROM base AS root
# For conveience if we need extras.
USER root

FROM base AS nonroot
# This is to give a safe default.