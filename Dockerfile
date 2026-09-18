# Jupyter image for MSD-LIVE with cerf pre-installed.
#
# Dependencies come from pyproject.toml (installed from this checkout, not a separate list, so the
# container cannot drift from the package metadata). The Zenodo package-data supplement is fetched at
# build time so notebooks run without network access.
#
# To test this container locally, run:
#   docker build -t im3sfa/cerf-msdlive .
#   docker run --rm -p 8888:8888 im3sfa/cerf-msdlive

# The upstream image publishes only moving tags (`latest`, `dev`); for a reproducible rebuild pass a
# digest, e.g. `--build-arg BASE_IMAGE=ghcr.io/msd-live/jupyter/python-notebook@sha256:<digest>`.
ARG BASE_IMAGE=ghcr.io/msd-live/jupyter/python-notebook:latest

# ---------------------------------------------------------------------------------------------------
# Stage 1: build a wheel from the checkout and resolve its dependencies
# ---------------------------------------------------------------------------------------------------
FROM ${BASE_IMAGE} AS builder

USER root

WORKDIR /src
COPY pyproject.toml README.md LICENSE ./
COPY cerf ./cerf

RUN python -m pip install --upgrade pip build \
 && python -m build --wheel --outdir /wheels . \
 && python -m pip wheel --wheel-dir /wheels /wheels/cerf-*.whl

# ---------------------------------------------------------------------------------------------------
# Stage 2: runtime image
# ---------------------------------------------------------------------------------------------------
FROM ${BASE_IMAGE}

USER root

COPY --from=builder /wheels /tmp/wheels

RUN python -m pip install --no-cache-dir --no-index --find-links /tmp/wheels cerf \
 && rm -rf /tmp/wheels

# Pre-install the example data supplement matching the installed cerf version (retries are built in;
# `--build-arg CERF_SKIP_DATA=1` skips this for offline builds).
ARG CERF_SKIP_DATA=0
RUN if [ "$CERF_SKIP_DATA" = "0" ]; then \
      python -c "import cerf; cerf.install_package_data(max_attempts=8, timeout=600)"; \
    fi

# Hand the environment back to the notebook user expected by the base image
USER ${NB_UID:-1000}
