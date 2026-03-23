FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# ---------------------------------------------------------------------------
# System packages (includes everything from REQUIRED_PACKAGES in common.py
# plus haproxy so the provisioner InstallPackages/InstallHAProxy steps skip)
# ---------------------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server openssh-client \
    python3 python3-pip python3-venv \
    curl wget openssl iproute2 qrencode dnsutils \
    ca-certificates gnupg sudo iptables ufw jq \
    socat unzip apt-transport-https \
    unattended-upgrades apt-listchanges \
    haproxy \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Docker CE (full package so InstallDocker step skips)
# ---------------------------------------------------------------------------
RUN install -m 0755 -d /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
      -o /etc/apt/keyrings/docker.asc && \
    chmod 644 /etc/apt/keyrings/docker.asc && \
    . /etc/os-release && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
      https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" \
      > /etc/apt/sources.list.d/docker.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      docker-ce docker-ce-cli containerd.io docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# Caddy (add repo + install so InstallCaddy step skips)
# ---------------------------------------------------------------------------
RUN curl -fsSL https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
      -o /etc/apt/keyrings/caddy-stable.asc && \
    chmod 644 /etc/apt/keyrings/caddy-stable.asc && \
    echo "deb [signed-by=/etc/apt/keyrings/caddy-stable.asc] https://dl.cloudsmith.io/public/caddy/stable/deb/debian any-version main" \
      > /etc/apt/sources.list.d/caddy-stable.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends caddy && \
    rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------------
# SSH on port 2222: self-connect via key auth (root@127.0.0.1)
# With --network host, port 22 is used by the CI runner's sshd.
# We run our sshd on 2222 and configure the SSH client accordingly.
# ---------------------------------------------------------------------------
RUN mkdir -p /run/sshd /root/.ssh && \
    ssh-keygen -A && \
    ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519 -N "" && \
    cat /root/.ssh/id_ed25519.pub >> /root/.ssh/authorized_keys && \
    chmod 700 /root/.ssh && \
    chmod 600 /root/.ssh/authorized_keys /root/.ssh/id_ed25519 && \
    sed -i 's/^#*Port .*/Port 2222/' /etc/ssh/sshd_config && \
    sed -i 's/^#*PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config && \
    printf 'Host 127.0.0.1\n  Port 2222\n  LogLevel ERROR\n' \
      > /root/.ssh/config && \
    chmod 600 /root/.ssh/config && \
    awk '{print "127.0.0.1 " $1 " " $2}' /etc/ssh/ssh_host_ed25519_key.pub \
      >> /root/.ssh/known_hosts && \
    awk '{print "[127.0.0.1]:2222 " $1 " " $2}' /etc/ssh/ssh_host_ed25519_key.pub \
      >> /root/.ssh/known_hosts && \
    chmod 600 /root/.ssh/known_hosts

# ---------------------------------------------------------------------------
# Mock systemctl (no systemd in Docker)
# ---------------------------------------------------------------------------
COPY tests/e2e/mock-systemctl.sh /usr/local/bin/systemctl
RUN chmod +x /usr/local/bin/systemctl

# ---------------------------------------------------------------------------
# Install meridian from source
# ---------------------------------------------------------------------------
COPY . /src
WORKDIR /src
RUN pip install --break-system-packages --no-cache-dir .

# ---------------------------------------------------------------------------
# Entry point: start sshd on 2222, verify self-SSH, then run E2E tests
# ---------------------------------------------------------------------------
COPY tests/e2e/run-e2e.sh /run-e2e.sh
RUN chmod +x /run-e2e.sh

WORKDIR /root
CMD ["/bin/bash", "-c", "/usr/sbin/sshd -e 2>/tmp/sshd.log && sleep 1 && ssh -o BatchMode=yes 127.0.0.1 echo 'sshd ok' && /run-e2e.sh || (echo 'E2E failed. sshd log:' && cat /tmp/sshd.log && exit 1)"]
