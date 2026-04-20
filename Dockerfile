FROM python:3.11-slim

# tc/netem
RUN apt-get update && apt-get install -y --no-install-recommends \
      iproute2 iputils-ping curl ca-certificates bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# болванки
COPY stubs/ .

# deps клиента
RUN pip install --no-cache-dir requests
RUN chmod +x entry-client.sh entry-server.sh
