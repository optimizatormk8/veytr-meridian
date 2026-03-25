# Backlog

Prioritized task list for Meridian development.
Version history is in [CHANGELOG.md](CHANGELOG.md).

---

## Manual / External

Things that require human action outside the codebase.

### Pre-launch (before public promotion)

- [ ] **Create 3-5 "good first issue" GitHub issues** — pull from P2/P3 items below to signal contributor-friendliness
- [ ] **Regenerate OG image** — `og.png` shows old domain `getmeridian.com`; needs `getmeridian.org`
- [ ] **Retake connection page screenshot** — `connection-page.png` shows stale domain in browser bar
- [ ] **Set GitHub social preview** — repo Settings > Social preview (depends on new OG image)
- [ ] **Write VPS onboarding guide** — ~300-word doc page: Hetzner/DigitalOcean, Debian 12, SSH keys, IP retrieval

### Launch channels (priority order)

- [ ] **r/selfhosted post** (~350k) — lead with architecture diagram, terminal SVG, demo page. Be upfront about no web UI
- [ ] **Show HN** — "Deploy an undetectable VLESS+Reality proxy in one command". Discuss uTLS, HAProxy SNI, threat model
- [ ] **r/opensource post** (~335k) — mission framing: "help people in censored regions share secure internet"
- [ ] **Niche communities** — r/iran, Telegram V2Ray/Xray groups (Persian, Chinese), r/privacy (engage, don't self-promote)

### Post-launch

- [ ] **Technical blog post** — HAProxy+Caddy+Xray architecture deep-dive. Cross-post to dev.to
- [ ] **"Meridian vs raw 3x-ui" comparison page** on website — captures search traffic
- [ ] **Respond to every comment** within 24h of launch posts

---

## P0 — Critical

### Anti-censorship

- [ ] **IP cert fingerprinting via Caddy catch-all** — active probers get Let's Encrypt IP cert on non-Reality SNI. Need cert strategy that mimics camouflage target or drops connection
- [ ] **XHTTP URL missing `sni=` in direct mode** — client infers SNI from raw IP, active probers can distinguish (`protocols.py:218`)
- [ ] **Relay topology exposed in connection pages** — relay + direct URLs together expose full topology (`connection-info.html.j2:172-188`)

### Product

- [ ] **`meridian client show NAME`** — regenerate/re-display connection info without recreating client
- [ ] **Client migration for rebuilds** — `meridian rebuild NEW_IP --from OLD_IP` or `meridian client migrate`

### Code quality

- [ ] **Magic email-prefix in stats script** — hardcodes `startswith('reality-')` instead of using `INBOUND_TYPES` (`provision/services.py:337-343`)
- [ ] **`ProvisionContext._state` untyped dict** — ~15 string keys with no schema. Promote to typed fields (`provision/steps.py:57-78`)

---

## P1 — High

### Security

- [ ] **`connection-info.html.j2` missing referrer meta** — local-save template leaks `file://` path via Referer
- [ ] **QR base64 not validated server-side** — `render.py` injects QR into `<img src>` without regex
- [ ] **`manifest.webmanifest.j2` no autoescape** — client name with `"` breaks JSON (`render.py:377`)
- [ ] **SW cache never invalidates** — hardcoded `CACHE_VERSION`. Embed hash during deployment (`sw.js:2`)
- [ ] **`window._meridianConfig` global** — exposes credentials to extensions. Use module-scoped variable
- [ ] **`install.sh` double curl-pipe-bash** — `uv` installer piped without checksum (`install.sh:49`)

### Anti-censorship

- [ ] **Manifest/title "Meridian" identifiable** — PWA install reveals circumvention tool. Make neutral/configurable
- [ ] **"Powered by Meridian" on connection pages** — add `--no-branding` or remove (`app.js:526-529`)
- [ ] **Default SNI `www.microsoft.com` monitored** — ASN mismatch detection. Make `meridian scan` the default
- [ ] **Docker pull fingerprinting** — `ghcr.io/mhsanaei/3x-ui` pull signals proxy setup
- [ ] **`spiderX: "/"` hardcoded** — fingerprint-able. Randomize or derive from camouflage target
- [ ] **`generated_at` timestamp** — reveals deployment time in connection page footer

### Product

- [ ] **VPS provider guide** — first blocker for Tier 1 "tech friends" (also in Manual section above)
- [ ] **Wizard hardening before SSH key validation** — can lock out password-only users
- [ ] **Connection page plain-language intro** — 2-3 trust-building sentences before "scan QR"
- [ ] **`client list` with usage stats** — last-seen, traffic totals via 3x-ui `getClientTraffics/{email}`
- [ ] **`client disable`/`client enable`** — panel API supports it, just needs CLI exposure
- [ ] **Proactive IP block detection** — server self-checks via ping endpoint, notifies via webhook/Telegram
- [ ] **Rebuild state transfer** — `meridian deploy NEW_IP --from OLD_IP` copies SNI, domain, clients

### Reliability

- [ ] **Provisioner no recovery guidance** — user left in inconsistent state. Add "resume from step N" messaging
- [ ] **`InstallDocker` skips regardless of image version** — no `docker compose pull` on re-deploy

### UX / Accessibility

- [ ] **No RTL CSS for Farsi** — directional properties need logical equivalents (`margin-inline-start/end`)
- [ ] **Toast "Copied" never translated** — hardcoded outside `#app`, `applyI18n()` never touches it
- [ ] **CSS "Click to copy" tooltip hardcoded EN** — CSS pseudo-element, untranslatable via `data-t`
- [ ] **iOS/Android deep link inconsistency** — hardcodes v2RayTun/Hiddify. Use `vless://` scheme
- [ ] **Toast no `role="alert"`** — invisible to screen readers
- [ ] **No ARIA landmarks or keyboard support** — all-div structure, no `tabindex`/`keydown`
- [ ] **QR alt text generic** — use `alt="QR code — Primary connection"` with protocol label
- [ ] **`<html lang="en">` hardcoded** — LTR flash on Farsi. Set server-side via template
- [ ] **Font sizes too small on mobile** — `.6rem` fails WCAG 1.4.4. Minimum `.75rem`
- [ ] **Language button touch targets too small** — under 44x44px minimum (WCAG 2.5.8)
- [ ] **CommandBuilder keyboard nav** — ARIA `tablist` missing arrow-key navigation
- [ ] **Language picker no `aria-pressed`** — active language visual-only
- [ ] **`document.execCommand('copy')` deprecated** — broken on iOS 16.4+

### Code quality

- [ ] **Silent template failures return `""`** — catch bare `Exception`, deploy empty HTML (`render.py:370,390`)
- [ ] **`upload_client_files()` should use base64** — `printf` may exceed `ARG_MAX` (`pwa.py:79`)
- [ ] **`pwa.py` mkdir unchecked** — disk full gives confusing downstream failures
- [ ] **Zero test coverage: upload pipeline** — security-sensitive shell construction untested
- [ ] **Zero test coverage: `DeployConnectionPage`** — ~80 lines URL+QR+stats untested
- [ ] **Zero test coverage: `_render_stats_script()`** — complex embedded Python untested
- [ ] **Caddy XHTTP block untested** — tests never pass `xhttp_path`/`xhttp_internal_port`
- [ ] **`_PWA_APPS` / `apps.json` sync untested** — CI validates template, not Python constant
- [ ] **Manifest color mismatch** — `#0c0e14` vs `#14161E` causes PWA splash flash
- [ ] **Caddy config duplication** — `_render_caddy_config()` and `_render_caddy_ip_config()` near-identical
- [ ] **Protocol card hero/non-hero duplication** — ~85 lines differ only by CSS class
- [ ] **`protocols` typed as `dict[str, Any]`** — forces runtime isinstance guards
- [ ] **ValueError instead of fail()** — `client.py:208,401,475` raise wrong exception
- [ ] **URL construction duplicated** — `DeployConnectionPage` duplicates `protocols.py` logic
- [ ] **Jinja2 dev-only but runtime-required** — `render.py` fallback untested
- [ ] **`SimpleNamespace(stdout=...)` QR hack** — template should use plain string

---

## P2 — Medium

### Security

- [ ] **IP-lookup leaks setup activity** — `curl ifconfig.me` visible to ISP/DPI. Self-host at `getmeridian.org/ip`
- [ ] **Panel cookie predictable path** — shared across concurrent processes. Use `tempfile.mkstemp`

### Anti-censorship

- [ ] **XHTTP path length predictable** — 16 chars is narrow entropy. Vary length or add prefix
- [ ] **`packet-up` XHTTP asymmetric traffic** — bursty upstream detectable. Consider `stream-up`
- [ ] **DNS `8.8.8.8` during provisioning** — monitored by censors. Use system resolver

### Product

- [ ] **Batch client add** — `meridian client add alice bob charlie`
- [ ] **Per-client traffic/IP limits** — `--limit-gb`, `--limit-ip` flags
- [ ] **Self-hosted ping endpoint** — for when `getmeridian.org` is blocked
- [ ] **Windows WSL setup guide** — doc page
- [ ] **`meridian server status`** — multi-server overview
- [ ] **`meridian test --via RELAY_IP`** — E2E test through relay
- [ ] **`meridian client export NAME`** — standalone HTML for offline sharing
- [ ] **`qrencode` install or louder failure** — include in install script

### Reliability

- [ ] **SSH `ConnectTimeout=5` too aggressive** — increase to 10s or add retry
- [ ] **No `docker compose pull` on re-deploy** — stale image when digest changes
- [ ] **`_wait_for_panel` SSH vs panel confusion** — polling breaks on transient SSH issues
- [ ] **E2E mocks systemctl** — service supervision never tested

### UX

- [ ] **Farsi question mark ASCII** — use `؟` not `?`
- [ ] **Multi-protocol jargon** — "XHTTP" meaningless to non-tech. Use "Connection 1 / 2"
- [ ] **`<title>` not updated on language switch** — stays English
- [ ] **"via {name}" hardcoded English** — needs translation
- [ ] **`index.html` not in SW precache** — first offline visit fails
- [ ] **Click-to-copy no keyboard support** — no `tabindex`/`keydown`
- [ ] **`apple-touch-icon` uses SVG** — iOS needs PNG
- [ ] **QR 200x200px marginal on Retina** — generate 400x400px
- [ ] **Stats strings English-only** — "Active now" not translated
- [ ] **Wizard `_confirm_scan()` fails silently on WSL**
- [ ] **Wizard no SSH user validation** — shell metacharacters accepted
- [ ] **Relay offer defaults to N** — hides useful feature
- [ ] **Docs links in translations** — point to `/docs/en/`
- [ ] **Landing i18n doesn't update `<title>`/OG** — shared links show English
- [ ] **Mobile nav keyboard broken** — no Escape handler/focus management
- [ ] **`innerHTML` XSS surface** — if translations ever loaded externally

### Code quality

- [ ] **`config.json` schema not validated in tests**
- [ ] **Measure test coverage** — `pytest --cov`, add badge to README
- [ ] **Unicode client names never tested** — Cyrillic/Farsi/CJK real-world scenarios
- [ ] **`confirm()` raises Exit(1) on "n"** — can't distinguish from failure
- [ ] **`_sync_credentials_to_server()` ignores SCP failures**
- [ ] **`_qrencode_warned` global poisons test isolation**
- [ ] **`InstallCaddy` 11-parameter constructor** — resolved from context anyway
- [ ] **Wizard/provisioner integration untested**
- [ ] **`detect_public_ip()` no caching** — adds 3-6s latency
- [ ] **Duplicate atomic-write** — `_save_relay_local()` duplicates `ServerCredentials.save()`

### Website

- [ ] **Live GitHub stars in trust bar** — shields.io badge or API fetch
- [ ] **Sitemap i18n hreflang** — `i18n` option in `sitemap()` config
- [ ] **Dark mode toggle** — system-preference only, no manual override
- [ ] **CSS sync activation** — `sync-template-css.mjs` in CI
- [ ] **Accordion body translations** — ~50 hardcoded EN keys
- [ ] **CommandBuilder i18n** — hint text hardcoded EN
- [ ] **GenAI images** — fresh OG, logo, favicon
- [ ] **Docs sidebar on mobile** — no nav below 860px
- [ ] **Footer `/version` endpoint** — fetch fails silently
- [ ] **Hero image no WebP/AVIF** — 30-50% byte savings
- [ ] **Font preload missing** — no `<link rel="preload">`
- [ ] **CommandBuilder RTL alignment** — 120px clips
- [ ] **`aria-current="page"` on nav links**

### Provisioner / Architecture

- [ ] Domain mode E2E test
- [ ] Provisioner unit tests (mock `conn.run()`)
- [ ] Credential file corruption test
- [ ] Extract shared: BBR/firewall, credential sync, connection page deploy, client name validation
- [ ] Consolidate UUID generation (`panel.py` + `provision/panel.py`)
- [ ] `console.fail()` hint_type type safety — `Literal["user", "system", "bug"]`
- [ ] `PROTOCOL_ORDER` consistency
- [ ] `urls.py`/`render.py` hardcoded protocol keys → generic dispatch
- [ ] Rename to "VLESS transport registry"
- [ ] Extract `PanelTransport` — separate SSH+curl from API
- [ ] `console.fail()` → `MeridianError` hierarchy
- [ ] Partial client add rollback
- [ ] Broad `except Exception` — `scan.py`, `render.py`, `update.py`
- [ ] Panel context manager — cookie leak on failure
- [ ] Subprocess timeout — `update.py:83-110`
- [ ] Jinja2 template caching — re-creates Environment per call
- [ ] N+1 panel calls — `find_inbound()` re-fetches list
- [ ] 14 untested modules
- [ ] `assert` in production — `provision/panel.py:223-224`
- [ ] `Inbound.clients`/`stream_settings` untyped
- [ ] `is_ipv4()` edge cases — use `ipaddress.ip_address()`

---

## P3 — Nice to have

- [ ] Audit log (client add/remove history)
- [ ] Password-protected connection pages
- [ ] Multi-server client management
- [ ] Connection page auto-test (try each URL, highlight working one)
- [ ] IPv6 support
- [ ] Inbound remark names generic (not "VLESS-Reality")
- [ ] RealiTLScanner cleanup on scan failure
- [ ] Landing page `<title>` neutral (not "Censorship-Resistant Proxy")
- [ ] HAProxy/Caddy `LimitNOFILE`
- [ ] `_is_on_server()` local IP enumeration instead of external HTTP
- [ ] Relay removal clean binary/config
- [ ] Getting-started "two minutes" → realistic "five minutes"
- [ ] WSL definition in docs
- [ ] Wizard SNI skip validation
- [ ] Wizard failure message truncation

---

## Icebox

- [ ] Key/credential rotation without reinstall
- [ ] Zero-to-VPN onboarding wizard on website
- [ ] Shell completion (typer built-in)
- [ ] Remove v1→v2 credential migration
- [ ] `conn.run()` → `RemoteConnection`/`LocalConnection`
- [ ] `check.py:run()` 234-line monolith
- [ ] `client.py:run_add()` 146 lines
- [ ] Caddy repo `any-version` codename

---

## Done

Collapsed — see [CHANGELOG.md](CHANGELOG.md) for details.

- **3.8.1** — Deploy version tracking + CLI/server mismatch warning, SECURITY.md fix, README docs alignment, CODE_OF_CONDUCT, homepage relay section + og:locale, PWA sub-url toggle + clock warning + flag emoji removal, trust bar cleanup, BACKLOG compaction
- **3.8.0** — PWA security/a11y/i18n (40 tests), landing page restructure, README positioning, install.sh fix, architecture SVG, locale links, reduced-motion, GitHub topics/discussions
- **3.7.4** — Caddy `handle_path` fix for PWA cache headers, mypy/lint fixes
- **3.7.2** — local mode, security hardening, reliability (19 items)
- **3.7.1** — HAProxy port fix
- **3.7.0** — website, provisioner hardening (9 items)
