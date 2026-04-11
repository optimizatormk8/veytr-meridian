FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl openssl ca-certificates jq bash procps iproute2 netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

CMD ["sleep", "infinity"]
