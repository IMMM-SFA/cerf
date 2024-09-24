# Stage 1: Build Stage
FROM quay.io/jupyter/minimal-notebook as builder

USER root

RUN apt-get update

# Set up GDAL so users on ARM64 architectures can build the Fiona wheels
# ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
# ENV C_INCLUDE_PATH=/usr/include/gdal
# RUN apt-get install -y \
#     build-essential \
#     gdal-bin \
#     libgdal-dev \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# Install cerf
RUN pip install --upgrade pip
RUN pip install cerf

# Stage 2: Final Stage
FROM quay.io/jupyter/minimal-notebook

USER root

# Install graphviz
RUN apt-get update
# RUN apt-get install -y graphviz

# Copy python packages installed/built from the builder stage
COPY --from=builder /opt/conda/lib/python3.11/site-packages /opt/conda/lib/python3.11/site-packages

# To test this container locally, run:
# docker build -t cerf .
# docker run --rm -p 8888:8888 cerf