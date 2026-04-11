#!/usr/bin/env bash
set -euo pipefail

mkdir -p /run/sshd /run/systemd/system /var/log/journal

if [ ! -f /etc/machine-id ]; then
  systemd-machine-id-setup >/dev/null 2>&1 || dbus-uuidgen --ensure=/etc/machine-id
fi

if [ -n "${AUTHORIZED_KEY:-}" ]; then
  mkdir -p /root/.ssh
  chmod 700 /root/.ssh
  printf '%s\n' "$AUTHORIZED_KEY" > /root/.ssh/authorized_keys
  chmod 600 /root/.ssh/authorized_keys
fi

if [ -n "${KNOWN_HOSTS:-}" ]; then
  mkdir -p /root/.ssh
  chmod 700 /root/.ssh
  printf '%s\n' "$KNOWN_HOSTS" > /root/.ssh/known_hosts
  chmod 600 /root/.ssh/known_hosts
fi

if [ -n "${HOSTS_APPEND:-}" ]; then
  printf '%s\n' "$HOSTS_APPEND" >> /etc/hosts
fi

mkdir -p /etc/systemd/system/docker.service.d
cat >/etc/systemd/system/docker.service.d/override.conf <<'UNIT'
[Service]
ExecStart=
ExecStart=/usr/bin/dockerd --host=unix:///var/run/docker.sock --iptables=false --storage-driver=vfs
UNIT

systemctl daemon-reload >/dev/null 2>&1 || true
systemctl enable ssh >/dev/null 2>&1 || true
systemctl enable docker >/dev/null 2>&1 || true

if [ -n "${EXTRA_BOOT_COMMANDS:-}" ]; then
  bash -lc "$EXTRA_BOOT_COMMANDS"
fi

exec /sbin/init
