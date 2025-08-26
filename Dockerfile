FROM continuumio/miniconda3:latest

LABEL maintainer="Tissue Extraction Pipeline"
LABEL description="Unified pipeline for tissue extraction from whole-slide images"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libglib2.0-dev \
    libvips-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    openslide-tools \
    && rm -rf /var/lib/apt/lists/*



COPY environment.yml /app/


RUN conda env create -f environment.yml && conda clean -afy


COPY unified_tissue_pipeline.py /app/
COPY README.md /app/


RUN mkdir -p /app/input /app/output /app/temp


ENV VIPS_CONCURRENCY=4
ENV VIPS_DISC_THRESHOLD=1gb
ENV OPENCV_IO_MAX_IMAGE_PIXELS=1073741824


ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "pipeline", "python", "/app/unified_tissue_pipeline.py"]

CMD ["--help"]
