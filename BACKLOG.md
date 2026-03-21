# Backlog

**Last updated:** 2026-03-21
**Version:** 3.2.0

---

## Strategic direction

**Ansible is deleted.** The Python provisioner is the only deployment engine. E2E tested: fresh setup, idempotent re-runs, client management, uninstall — all verified across 2 full cycles on a real Ubuntu 24.04 server with non-root sudo user.

**We are keeping 3x-ui.** Coupling is contained in `PanelClient`.

---

## What shipped in v3.1.0–3.2.0

- Python provisioner engine (15 steps replacing all Ansible roles)
- Ansible fully deleted (-2,825 lines): playbooks, roles, ansible.py, CI jobs
- Uninstall provisioner (replaces playbook-uninstall.yml)
- Protocol foundation (ProtocolURL, dict registry, DRY base class)
- Output split into urls.py / render.py / display.py
- Error taxonomy, sudo escalation, PanelClient context manager
- E2E tested: 2 full setup→client→uninstall→setup cycles on real server
- README emotional hook, common scenarios, AI docs fixes

---

## Next up

### Provisioner hardening

- [ ] Domain mode E2E test (HAProxy + Caddy + WSS on a server with domain)
- [ ] Provisioner unit tests (mock `conn.run()`, test idempotency checks)
- [ ] Domain prompt yes/no gate (replace `Domain [skip]:`)

### Scale features

- [ ] Batch client add (`meridian client add alice bob charlie`)
- [ ] Client migration for rebuilds (detect clients on old server, re-create)
- [ ] Cross-server `meridian status`
- [ ] Per-client traffic/IP limits (`--limit-gb`, `--limit-ip`)

---

## Icebox

- [ ] Subscription URL support
- [ ] Key/credential rotation without reinstall
- [ ] Proactive IP block notification (Telegram/webhook)
- [ ] Zero-to-VPN onboarding wizard on website
- [ ] Password-protected connection info page
- [ ] Shell completion (typer built-in)
- [ ] Website section reorder
- [ ] Deployed version in diagnostics
- [ ] "Broke after update" issue template
