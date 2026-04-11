#!/usr/bin/env bash
set -euo pipefail

ROOT=/workspace
OUT=$ROOT/tests/systemlab/output/device
mkdir -p "$OUT"

apt-get update -qq >/dev/null
apt-get install -y -qq python3 >/dev/null
python3 - <<'PY'
from meridian.credentials import ServerCredentials
from meridian.xray_client import build_test_configs
from pathlib import Path
import json

creds = ServerCredentials.load(Path('/workspace/tests/systemlab/output/shared/proxy.yml'))
configs = build_test_configs(creds)
selected = None
for label, cfg, expect in configs:
    if label == 'Reality via relaylab':
        selected = (label, cfg, expect)
        break
if selected is None:
    for label, cfg, expect in configs:
        if label.startswith('Reality via '):
            selected = (label, cfg, expect)
            break
if selected is None:
    raise SystemExit('no relay reality config found')
Path('/workspace/tests/systemlab/output/device/config.json').write_text(json.dumps(selected[1]))
Path('/workspace/tests/systemlab/output/device/label.txt').write_text(selected[0])
PY

XRAY_VERSION=$(python3 - <<'PY'
from meridian.config import XRAY_VERSION
print(XRAY_VERSION)
PY
)
ASSET="Xray-linux-64.zip"
URL="https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/${ASSET}"
curl -fsSL "$URL" -o /tmp/xray.zip
python3 - <<'PY'
import zipfile
with zipfile.ZipFile('/tmp/xray.zip') as zf:
    with zf.open('xray') as src, open('/usr/local/bin/xray', 'wb') as dst:
        dst.write(src.read())
PY
chmod +x /usr/local/bin/xray

/usr/local/bin/xray run -c /workspace/tests/systemlab/output/device/config.json >"$OUT/xray.stdout.log" 2>"$OUT/xray.stderr.log" &
XRAY_PID=$!
cleanup() {
  kill "$XRAY_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

for _ in $(seq 1 40); do
  if nc -z 127.0.0.1 $(python3 - <<'PY'
import json
print(json.load(open('/workspace/tests/systemlab/output/device/config.json'))['inbounds'][0]['port'])
PY
); then
    break
  fi
  sleep 0.5
done

SOCKS_PORT=$(python3 - <<'PY'
import json
print(json.load(open('/workspace/tests/systemlab/output/device/config.json'))['inbounds'][0]['port'])
PY
)

curl --socks5 127.0.0.1:${SOCKS_PORT} -sS http://echo-service:8080/device-check | tee "$OUT/echo.json"
python3 - <<'PY'
import json
from pathlib import Path
body = json.loads(Path('/workspace/tests/systemlab/output/device/echo.json').read_text())
client_ip = body.get('client_ip', '')
if not client_ip.startswith('172.'):
    raise SystemExit(f'unexpected client_ip: {client_ip}')
print(client_ip)
PY
