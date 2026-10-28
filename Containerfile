FROM docker.io/library/python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
COPY sdwire ./sdwire
RUN pip install --no-cache-dir .

ENTRYPOINT ["sdwire"]
CMD ["--help"]
