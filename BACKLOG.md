# Backlog

Prioritized task list for Meridian development.
Version history is in [CHANGELOG.md](CHANGELOG.md).

---

## Manual / External

Things that require human action outside the codebase.

### Housekeeping

- [ ] **Create 3-5 "good first issue" GitHub issues** — pull from P2 items below to signal contributor-friendliness
- [ ] **Regenerate OG image** — `og.png` shows old domain `getmeridian.com`; needs `getmeridian.org`
- [ ] **Retake connection page screenshot** — `connection-page.png` shows stale domain in browser bar
- [ ] **Set GitHub social preview** — repo Settings > Social preview (depends on new OG image)
- [ ] **Write VPS onboarding guide** — ~300-word doc page: Hetzner/DigitalOcean, Debian 12, SSH keys, IP retrieval

### Launch channels (priority order)

- [x] **Вастрик.Клуб** — [launched 2026-04-02](https://vas3k.club/project/31264/), 78 upvotes, 3k+ views, 100+ GitHub stars overnight
- [ ] **r/selfhosted post** (~350k) — lead with architecture diagram, terminal SVG, demo page. Be upfront about no web UI
- [ ] **Show HN** — "Deploy an undetectable VLESS+Reality proxy in one command". Discuss uTLS, HAProxy SNI, threat model
- [ ] **r/opensource post** (~335k) — mission framing: "help people in censored regions share secure internet"
- [ ] **Censorship expert TG channel post** — author of [state-of-usa-itd](https://habr.com/ru/articles/1014038/) offered to post about Meridian
- [ ] **Niche communities** — r/iran, Telegram V2Ray/Xray groups (Persian, Chinese), r/privacy (engage, don't self-promote)

### Post-launch

- [ ] **Technical blog post** — nginx+Xray architecture deep-dive. Cross-post to dev.to
- [ ] **"Meridian vs raw 3x-ui" comparison page** on website — captures search traffic
- [ ] **Respond to every comment** within 24h of launch posts

---

## P0 — Critical

### Anti-censorship

- [ ] **Relay SNI mismatch** — relay in RU zone inherits exit node's SNI (e.g. microsoft.com). Client connecting to a Russian IP with Microsoft SNI is unrealistic and detectable. Relay deploy should scan its own IP range and pick a locally plausible SNI, independent of exit node
- [ ] **IP cert fingerprinting via nginx catch-all** — active probers get Let's Encrypt IP cert on non-Reality SNI. Need cert strategy that mimics camouflage target or drops connection
- [ ] **Fix XHTTP nginx path mismatch** — align URL generation, Xray config, and nginx routing so both exact-path and slash-path requests hit the XHTTP upstream instead of falling through to stock 404s

### Product

- [ ] **Client migration for rebuilds** — `meridian rebuild NEW_IP --from OLD_IP` or `meridian client migrate`
- [ ] **Eliminate state split-brain between local cache and server** — local `proxy.yml` currently becomes authoritative once present because `fetch_credentials()` stops at any cached file, causing stale overwrites across multiple machines and non-root on-server divergence between `~/.meridian` and `/etc/meridian`. Define a single source of truth, force refresh before all write commands including relay lifecycle commands, and make sync failures blocking before handoff files/pages are published
- [ ] **Redeploy must update live state before publishing new handoff state** — fix paths where redeploy updates saved credentials/pages without updating the live server: Reality SNI changes, relay SNI routing failures, and other config drift cases. Never hand out URLs/pages the server is not actually serving
- [ ] **Partial panel recovery must preserve existing clients and relays** — `ConfigurePanel` recovery currently nukes 3x-ui state and recreates only baseline inbounds. Recovery should reconstruct all known clients, relay-specific inbounds, and hosted pages from credentials instead of silently deleting working access

### Security / Supply Chain

- [x] **Pin release artifacts to the CI-passed commit** — `release.yml` now checks out `github.event.workflow_run.head_sha` in all release jobs (Pages, tag/release creation, PyPI publish)
- [ ] **Replace mutable install/update trust chain with pinned, verified artifacts** — stop relying on branch-tip `curl | bash` and raw GitHub fallback. Silent patch auto-upgrades were removed from normal CLI use; remaining work is to tie install/update to release artifacts with checksum verification and keep upgrades explicit
- [ ] **Stop executing unsigned remote scanner binaries as root** — `meridian scan` should use a pinned release plus cryptographic verification, or vendor the scanner. `releases/latest` plus ELF/size checks are not enough for a hardening tool

---

## P1 — High

### Security

- [x] **SSH password auth not hardened during provisioning** — provisioning now writes an authoritative Meridian drop-in under `/etc/ssh/sshd_config.d/99-meridian.conf` and validates the effective config with `sshd -T`
- [ ] **Firewall cleanup deletes user's custom rules** — `ConfigureFirewall` removes ALL TCP ports not in `{22, 443, 80}`, silently deleting alternate SSH ports, monitoring, or relay listen ports. Should only delete Meridian-managed ports or warn before removing unexpected rules (`common.py:441-458`)
- [ ] **Remove public 3x-ui management from the shared 443 identity** — hiding the panel behind a random path is weaker than removing it from the public nginx identity entirely. Move management off the main camouflage surface or require an explicit operator-only access path

### Anti-censorship

- [ ] **Default SNI `www.microsoft.com` monitored** — ASN mismatch detection. Make `meridian scan` the default
- [ ] **Make probe/check tooling mode-aware** — domain mode intentionally serves a real domain cert, but current verification treats that as a stealth leak. Align `probe` and TLS checks with supported deployment modes so users do not get false alarms from valid configs

### Product

- [ ] **VPS provider guide** — first blocker for Tier 1 "tech friends"
- [ ] **Auto SSH key setup** — when VPS only has password auth, auto-generate key, copy via `ssh-copy-id`, and proceed. Eliminates manual key setup step before deploy
- [ ] **Telegram bot for client management** — add/revoke clients, view stats without SSH. Mobile-friendly for "not at computer" use case
- [ ] **Post-deploy Cloudflare setup guidance** — after domain mode deploy, print step-by-step Cloudflare DNS/SSL setup in CLI output
- [ ] **Add Happ and ShadowRocket to connection page** — popular cross-platform clients, already support VLESS subscription URLs
- [ ] **Wizard hardening before SSH key validation** — can lock out password-only users
- [ ] **Connection page plain-language intro** — 2-3 trust-building sentences before "scan QR"
- [ ] **`client list` with usage stats** — last-seen, traffic totals via 3x-ui `getClientTraffics/{email}`
- [ ] **`client disable`/`client enable`** — panel API supports it, just needs CLI exposure
- [ ] **Proactive IP block detection** — server self-checks via ping endpoint, notifies via webhook/Telegram
- [ ] **Rebuild state transfer** — `meridian deploy NEW_IP --from OLD_IP` copies SNI, domain, clients
- [ ] **Make destructive mutations transactional** — `client remove`, `relay deploy`, `relay remove`, and teardown should not delete local state, registry entries, hosted pages, or print success after partial remote failures. Either complete remote cleanup or stop and leave state unchanged with a recovery path
- [ ] **Require explicit server identity for risky commands** — enforce unique server aliases, separate deployer aliasing from recipient-facing branding, and add clearer target confirmation for destructive/stateful commands. Implicit local-mode detection and single-server auto-select are acceptable for read-only commands at most; mutating commands are too easy to mis-target today
- [ ] **Make server aliases unique and trustworthy** — reject duplicate names, show host+user in confirmations/output, and require confirmation before `server remove` deletes cached credentials
- [ ] **Regenerate all hosted client pages when shared server state changes** — branding, domain, SNI, relay topology, and other handoff-affecting redeploy changes must update every existing hosted page/subscription, not just the first/default client
- [ ] **Unify deployer-facing and recipient-facing naming** — `--display-name` and `--server` currently model different identities but docs and UX blur them together. Either unify them or expose the distinction clearly in commands and docs
- [ ] **Hosted connection page must stay self-hosted in recovery flows** — remove `getmeridian.org/ping` dependence from the PWA, legacy hosted HTML, and CLI guidance; remove App Store fallback redirects and other third-party install/troubleshooting dependencies from the critical handoff path so import/recovery does not leak server metadata externally

### Reliability

- [ ] **WARP must be health-gated and reversible** — only insert WARP as the default outbound once it is actually connected, support full rollback on `--no-warp`, and avoid leaving users in a false-success state where clients connect but outbound traffic is dead
- [ ] **Domain mode must support safe steady-state redeploys behind orange-cloud** — current redeploy logic expects the DNS record to point directly at the server IP, conflicting with the docs' normal post-deploy Cloudflare setup
- [x] **Persist relay SSH user across lifecycle commands** — `relay check` and `relay remove` now reuse the stored relay registry user by default, with tests
- [x] **Preserve forward-compatible nested credential fields** — nested unknown fields under server/panel/protocols/clients/relays/branding now round-trip via per-dataclass `_extra` preservation, with tests. Remaining follow-up: auxiliary ingestion paths like `merge_clients_file()` should preserve future per-client fields too

### Testing

- [ ] **Make E2E fail on idempotency and redeploy regressions** — the current shell E2E run explicitly tolerates failures in the repo's core promise: safe re-run and clean redeploy, converting them into warnings in `tests/e2e/run-e2e.sh`. These paths should be hard failures in CI
- [ ] **Add real-host coverage for production-sensitive branches** — current E2E bypasses cert issuance, systemd management, nginx bootstrap, and other documented sharp edges. Add coverage that exercises the real operational branches instead of the stubs
- [ ] **Add end-to-end coverage for domain mode, WARP, and relay migration** — these features are currently validated mostly via mocks/render tests, which is not enough for deployment-changing behavior
- [ ] **Add dedicated tests for recovery and migration paths** — especially `ConfigurePanel` partial recovery, relay nginx migration for pre-existing servers, stale-state conflict resolution, repeated protocol round-trips (`reality`/`wss`/`xhttp`), merged client-file paths, and write-command behavior under failed refresh/sync

---

## P2 — Medium

### Security

- [ ] **`innerHTML` XSS surface** — risk if translations ever loaded externally

### Product

- [ ] **Batch client add** — `meridian client add alice bob charlie`
- [ ] **Per-client traffic/IP limits** — `--limit-gb`, `--limit-ip` flags
- [ ] **Self-hosted ping endpoint** — make this the default troubleshooting path from hosted client pages so connection testing still works when `getmeridian.org` is blocked and doesn't leak server metadata externally
- [ ] **Windows WSL setup guide** — doc page
- [ ] **`meridian server status`** — multi-server overview
- [ ] **`meridian test --via RELAY_IP`** — E2E test through relay
- [ ] **`meridian client export NAME`** — standalone HTML for offline sharing
- [ ] **OpenWRT router auto-deploy** — deploy client config directly to OpenWRT routers
- [ ] **Relay on server with existing nginx** — support deploying relay alongside an existing web server on port 443
- [ ] **WebRTC leak warning on connection page** — WebRTC leaks are client-side (browser discovers local IPs via OS APIs, bypassing the proxy entirely). Server-side fixes don't help — traffic never reaches Xray. Add amber warning box to connection page with: 1) link to browserleaks.com/webrtc leak test, 2) per-app guidance (v2rayNG: Global mode, Hiddify: route all connections), 3) browser extension recommendation. Same pattern as clock-sync warning
- [ ] **Replace `qrencode` binary with Python `segno` package** — eliminates system dependency

### Reliability

- [ ] **`_wait_for_panel` SSH vs panel confusion** — polling breaks on transient SSH issues
- [ ] **Xray process accumulation on `test_connection()` timeouts** — orphan processes not cleaned up when `_wait_for_port()` times out (`xray_client.py:305-350`)

### Testing

- [ ] **12 source modules have zero tests** — remaining gaps: `ping.py`, `check.py`, `scan.py`, `docker.py`, `config.py`, `display.py`, `ai.py`, `models.py`, `server.py`, `uninstall.py`, `provision/uninstall.py`

### UX

- [ ] **Multi-protocol jargon** — "XHTTP" meaningless to non-tech. Use "Connection 1 / 2"
- [ ] **`index.html` not in SW precache** — first offline visit fails
- [ ] **`apple-touch-icon` uses SVG** — iOS needs PNG
- [ ] **Wizard `_confirm_scan()` fails silently on WSL**
- [x] **Use canonical `subscription_url` in the PWA** — `app.js` now prefers `config.subscription_url`, with fallback only when the field is absent. Remaining follow-up: treat missing `subscription_url` as a rendering/config bug instead of silently masking routing drift

### Website

- [ ] **Live GitHub stars in trust bar** — shields.io badge or API fetch
- [ ] **Dark mode toggle** — system-preference only, no manual override
- [ ] **Docs sidebar on mobile** — no nav below 860px
- [ ] **Validate executable docs examples, not just flag tables** — CI currently misses broken README/deploy/recovery/domain-mode commands and behavior drift. Add validation for high-traffic command examples and claims across docs surfaces

---

## Icebox

- [ ] **Amnezia-style app deploy** — download app, enter VPS ip:user:password, auto-deploy without knowing SSH. Full GUI wrapper around `meridian deploy`
- [ ] **Meridian-branded cross-platform client app** — fork Hiddify (Flutter, sing-box, open source, 28k stars) into a stripped-down Meridian client. Subscription URL as primary flow: open app → paste URL / scan QR → connected. Happ is NOT open source (can't fork)
- [ ] **Key/credential rotation without reinstall**
- [ ] **Zero-to-VPN onboarding wizard on website**
- [ ] **Shell completion** — typer built-in
- [ ] **Remove v1→v2 credential migration** — dead code
- [ ] **Remove all Caddy and HAProxy code** — we use nginx, these are dead paths
- [ ] **Accessibility + i18n pass** — RTL CSS, ARIA landmarks, keyboard nav, touch targets, screen reader support, translation completeness (batched from ~20 items)

---

## Done

Collapsed — see [CHANGELOG.md](CHANGELOG.md) for details.

- **3.14** — `client show`, WARP flag, stats script fix, `--sni` plumbing, docker pull on re-deploy
- **Review loop (worktree)** — release workflow pinned to CI-passed SHA, nested credential field round-tripping preserved, PWA honors canonical `subscription_url`, client + relay remove paths fail closed on refresh/sync, silent patch auto-upgrade removed, sshd hardening moved to an authoritative drop-in with `sshd -T` validation, relay lifecycle commands reuse stored relay SSH users
- **3.8.1** — Deploy version tracking, SECURITY.md, CODE_OF_CONDUCT, PWA sub-url toggle + clock warning, trust bar cleanup
- **3.8.0** — PWA security/a11y/i18n (40 tests), landing page, install.sh, architecture SVG, reduced-motion
- **3.7** — Local mode, security hardening (19 items), Caddy/HAProxy fixes, website, provisioner hardening
- **Code quality sprint** — socket leaks, nginx 444, IPv6 URLs, WARP/ufw return codes, port conflict check, SSRF guard, exception handlers, SystemExit refactor, 80 new tests (branding, xray_client, render templates)
