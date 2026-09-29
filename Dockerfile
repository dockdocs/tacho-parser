ROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN git clone --depth 1 https://github.com/Syax89/DDDTachograph_Reader.git reader

WORKDIR /app/reader
RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir flask gunicorn

WORKDIR /app
COPY server.py .

ENV PORT=8080
EXPOSE 8080

CMD ["gunicorn", "-b", "0.0.0.0:8080", "--timeout", "180", "server:app"]
