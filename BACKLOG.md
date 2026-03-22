# Backlog

Prioritized task list for Meridian development.
Version history is in [CHANGELOG.md](CHANGELOG.md).

---

## Next up

### Website (getmeridian.org)

- [ ] **Dark mode toggle** — currently system-preference only, no manual override
- [ ] **CSS sync activation** — add `/* SYNC:START */` / `/* SYNC:END */` markers to `connection-info.html.j2`, run `sync-template-css.mjs` in CI
- [ ] **Accordion body translations** — Reference section content inside accordions is hardcoded EN (~50 keys needed)
- [ ] **CommandBuilder status messages i18n** — interactive hint text is hardcoded EN
- [ ] **GenAI images** — replace old screenshots with fresh OG, logo, favicon, connection page, architecture diagram (prompts in session notes)

### Provisioner hardening

- [ ] Domain mode E2E test (HAProxy + Caddy + WSS on a server with domain)
- [ ] Provisioner unit tests (mock `conn.run()`, test idempotency) — priority: `ConfigurePanel`, `CreateRealityInbound`, `LoginToPanel`
- [ ] Credential file corruption test (truncated/malformed YAML)

### Architecture debt

- [ ] Type `ProvisionContext` inter-step state — promote dict keys to typed Optional fields
- [ ] Make protocol abstraction honest — rename to "VLESS transport registry" (not truly protocol-agnostic)
- [ ] Extract `PanelTransport` protocol — separate SSH+curl transport from 3x-ui API semantics
- [ ] `console.fail()` → domain exceptions — `MeridianError` hierarchy, catch at CLI boundary
- [ ] Partial client add rollback (if Reality succeeds but WSS fails, clean up)
- [ ] Delete stale `output.py` legacy facade

### Security hardening

- [ ] SSH host key verification — `accept-new` enables TOFU MitM. Switch to prompt-based or `--accept-new-host-key` flag
- [ ] Docker image digest pinning — pin to `@sha256:...`
- [ ] RealiTLScanner checksum verification — binary downloaded without integrity check
- [ ] `confirm()` defaults to yes without TTY — destructive ops should default to "no"

### UX improvements

- [ ] `meridian client show NAME` — regenerate connection info without recreating the client
- [ ] `client list` usage stats from 3x-ui API
- [ ] IPv6 support
- [ ] Subscription URL support (`subEnable` for auto-config on IP change)

### Scale features

- [ ] Batch client add (`meridian client add alice bob charlie`)
- [ ] Client migration for rebuilds (detect clients on old server, re-create)
- [ ] Per-client traffic/IP limits (`--limit-gb`, `--limit-ip`)

---

## Icebox

- [ ] Key/credential rotation without reinstall
- [ ] Proactive IP block notification (Telegram/webhook)
- [ ] Zero-to-VPN onboarding wizard on website
- [ ] Password-protected connection info page
- [ ] Shell completion (typer built-in)
- [ ] Remove v1→v2 credential migration (sunset old format)
- [ ] `conn.run()` complexity — split into `RemoteConnection`/`LocalConnection`
- [ ] `check.py:run()` 234-line monolith — extract checks into individual functions
- [ ] `client.py:run_add()` 146 lines — extract helper functions
