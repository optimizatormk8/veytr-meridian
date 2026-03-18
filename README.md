# Meridian

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/uburuntu/meridian)](https://github.com/uburuntu/meridian/stargazers)

One command deploys a censorship-resistant proxy server. Invisible to DPI, active probing, and TLS fingerprinting.

```bash
curl -sS https://raw.githubusercontent.com/uburuntu/meridian/main/setup.sh | bash
```

- **Undetectable** — VLESS+Reality makes your server look like microsoft.com to any probe
- **2 minutes** — interactive wizard handles everything: Docker, Xray, firewall, TLS
- **QR code output** — send an HTML file to whoever needs it, they scan and connect
- **Idempotent** — safe to re-run, picks up where it left off
- **Relay chain** — two-server mode bypasses IP whitelisting

**What you need:** A Debian/Ubuntu VPS with root SSH key access. The script handles the rest.

**Uninstall:** `curl -sS https://raw.githubusercontent.com/uburuntu/meridian/main/setup.sh | bash -s -- --uninstall`

**Full docs:** [meridian.msu.rocks](https://meridian.msu.rocks)
