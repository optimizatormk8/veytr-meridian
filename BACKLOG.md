# Backlog

**Last updated:** 2026-03-21
**Version:** 3.0.1
**Source:** Five-reviewer grand assessment (architecture, UX, code quality, Ansible, docs)

---

## Strategic direction

**We are moving off Ansible.** The CLI already bypasses Ansible for client management (pure Python via PanelClient). The remaining Ansible layer creates a dual-language maintenance tax: every protocol, credential field, and URL format lives in both Python and YAML. The goal is a single-language Python codebase where deployment, client management, and output are all driven by the same protocol abstractions.

**We are keeping 3x-ui.** It's powerful, actively maintained, and provides a web UI that keeps power users on Meridian. The coupling is well-contained in `PanelClient` — we strengthen that boundary, not replace it.

**Foundation first.** Before migrating roles, we build the provisioning primitives that give us Ansible's guarantees in Python: idempotent steps with structured tracing, actionable error output, and AI-ready diagnostics.

---

## Execution Plan (DAG)

Each wave has 1-2 agents max with **non-overlapping file ownership** to prevent merge conflicts. Agents run in isolated git worktrees — each gets a clean copy of the repo on a separate branch. Between waves, branches merge to main.

```
Wave 0: Protocol Foundation ──────────────────────────┐
  1 agent · protocols.py, models.py                    │
                                                       ▼
Wave 1: Bugs + Error Handling ────────────────────────┐
  2 agents (non-overlapping files)                     │
  A: Ansible YAML only                                 │
  B: Python only (console, client, output, update)     │
                                                       ▼
Wave 2: Output Restructure + Testing ─────────────────┐
  2 agents                                             │
  A: output.py → urls.py + render.py + display.py      │
  B: tests/ only                                       │
                                                       ▼
Wave 3: Provisioner Foundation ───────────────────────┐
  2 agents                                             │
  A: provisioner.py (new) — Step/StepResult + common   │
  B: provisioner_xray.py (new) — panel config steps    │
                                                       ▼
Wave 4: Migration Completion ─────────────────────────┐
  2 agents                                             │
  A: provisioner_services.py — caddy + haproxy         │
  B: setup.py rewire + ansible.py deletion + CI        │
                                                       ▼
Wave 5: UX + Docs ───────────────────────────────────┐
  2 agents                                             │
  A: CLI UX (wizard, prompts, error messages)          │
  B: docs/ + README + AI docs                          │
                                                       ▼
Wave 6: Scale Features
  batch client ops · client migration · status command
```

### How agents use worktrees

Each agent runs in an **isolated git worktree** (`isolation: "worktree"`). This gives it a clean copy of the repo on a new branch, so two agents can edit files simultaneously without conflicts.

**Rules for agents within a wave:**
- Each agent owns specific files/directories — never edit files outside your ownership
- Commit your changes with descriptive messages before finishing
- Your branch will be merged to main between waves

**Between waves:** All agent branches are merged to main. The next wave's agents start from the merged state. If a merge conflict occurs, it means file ownership was violated — fix the wave design, don't force-merge.

---

## Wave 0 — Protocol Foundation

**1 agent.** This is the critical path — every subsequent wave depends on these abstractions being right.

**File ownership:** `src/meridian/protocols.py`, `src/meridian/models.py` (new), `tests/test_protocols.py`

- [ ] **Move `Inbound` dataclass from `panel.py` to `models.py`** — breaks coupling between protocol abstraction and panel API client. Both `protocols.py` and `panel.py` import from `models.py`.
- [ ] **DRY `client_settings()` into base `Protocol` class** — the three identical implementations differ only by `self.inbound_type.flow`. One method on the ABC, zero copy-paste.
- [ ] **Create `ProtocolURL` dataclass** — replaces hardcoded `ClientURLs(reality, xhttp, wss)` with generic `list[ProtocolURL]` where each entry has `key`, `label`, `url`. This is the key enabler for protocol-agnostic output.
- [ ] **Make `get_protocol()` O(1)** — change `PROTOCOLS` from list to `dict[str, Protocol]`. Keep `PROTOCOL_ORDER: list[str]` for iteration order.
- [ ] **Update `test_protocols.py`** — add tests for base class `client_settings()`, ProtocolURL construction, dict-based registry.

## Wave 1 — Bugs + Error Handling

**2 agents.** Non-overlapping file ownership.

### Agent A: Ansible fixes (YAML only)

**File ownership:** everything under `src/meridian/playbooks/roles/`, `src/meridian/playbooks/playbook.yml`

- [ ] **FIX: XHTTP `client_total_bytes` division** — `configure_reality_xhttp.yml:59` must divide by 1073741824 like Reality/WSS do.
- [ ] **FIX: Validate `json.success` on default panel login** — `apply_panel_settings.yml` must assert `default_login.json.success == true` and fail with actionable message if credentials already changed.
- [ ] **SEC: Add `| quote` filter to QR shell tasks** — `caddy/tasks/main.yml:114-136` and `shared/tasks/generate_client_output.yml:69-91` interpolate `reality_sni` without shell quoting.
- [ ] **FIX: Move DNS check to pre_tasks** — currently in Caddy role, fails after Docker+Xray are already deployed. Move to `playbook.yml` pre_tasks so it fails fast.

### Agent B: Python error handling + code fixes

**File ownership:** `src/meridian/console.py`, `src/meridian/commands/client.py`, `src/meridian/output.py`, `src/meridian/update.py`, `src/meridian/ssh.py`

- [ ] **Replace `assert` with explicit checks** — `client.py:57,74,138,311` and `output.py:65,72,79`. Use `if x is None: fail(...)` or `raise ValueError(...)`.
- [ ] **Add error taxonomy to `fail()`** — add `hint_type` parameter: `"user"` (input errors — no GitHub link), `"system"` (infrastructure errors — suggest diagnostics), `"bug"` (unexpected — show GitHub link). Default to `"bug"` for backward compat.
- [ ] **Fix silent `except Exception` blocks** — `output.py:205,274` and `update.py:27,60`. Add `import warnings; warnings.warn(...)` so template regressions and update errors are visible in debug.
- [ ] **Fix type annotations** — `client.py`'s `_make_panel(conn: object)` and `_sync_credentials_to_server(resolved: object)`. Use `TYPE_CHECKING` guard to import real types.
- [ ] **Make `PanelClient` a context manager** — `__enter__`/`__exit__` replacing `try/finally: panel.cleanup()` pattern in all callers.
- [ ] **DRY SSH options** — extract `SSH_OPTS` constant in `ssh.py`, use in `_ssh_opts`, `fetch_credentials` SCP, and `client.py`'s `_sync_credentials_to_server`.

## Wave 2 — Output Restructure + Testing

**2 agents.** Agent A restructures output using Wave 0's `ProtocolURL`. Agent B writes tests against the new interfaces.

### Agent A: Output restructure

**File ownership:** `src/meridian/output.py` (→ split into new files), `src/meridian/commands/client.py` (update imports only)

- [ ] **Split `output.py` into focused modules:**
  - `urls.py` — `build_protocol_urls()` returning `list[ProtocolURL]`, QR generation functions
  - `render.py` — HTML + text file generation, Jinja2 template rendering (replace `type("obj",...)` hack with `SimpleNamespace`)
  - `display.py` — terminal output (`print_terminal_output`)
- [ ] **Gracefully degrade HTML when qrencode missing** — hide QR `<div>` when base64 data is empty string, instead of rendering broken `<img>`.
- [ ] **Use `list[ProtocolURL]` throughout** — all output functions iterate the protocol list generically. No more `if urls.xhttp:` branching.

### Agent B: Testing

**File ownership:** `tests/` only

- [ ] **Add tests for `client.py` command functions** — `run_add`, `run_list`, `run_remove` with mocked `PanelClient` and `ServerConnection`. Test credential update, file generation, server sync.
- [ ] **Convert `render_templates.py` to pytest** — use `pytest.mark.parametrize` over auto-discovered templates. Failures show in test suite, not separate make target.
- [ ] **DRY resolve+connect+fetch boilerplate** — extract shared helper in `commands/resolve.py`, test it.

## Wave 3 — Provisioner Foundation

**2 agents.** Build the Python provisioning engine that replaces Ansible.

### Agent A: Step abstraction + common/docker

**File ownership:** `src/meridian/provision/` (new package: `__init__.py`, `steps.py`, `common.py`, `docker.py`)

- [ ] **Design `Step` protocol and `StepResult` dataclass:**
  ```python
  @dataclass
  class StepResult:
      name: str           # "Install Docker"
      status: str         # "ok" | "changed" | "skipped" | "failed"
      detail: str         # Human-readable detail for tracing
      duration_ms: int    # Wall time

  class Step(Protocol):
      name: str
      def run(self, conn: ServerConnection, ctx: ProvisionContext) -> StepResult: ...
      def check(self, conn: ServerConnection, ctx: ProvisionContext) -> bool: ...  # idempotency check
  ```
- [ ] **`ProvisionContext` dataclass** — carries IP, user, domain, creds, accumulated results. Replaces Ansible's variable namespace.
- [ ] **`Provisioner` runner** — executes `list[Step]`, collects `list[StepResult]`, prints streaming progress (Rich spinner per step), generates trace log for `--ai` diagnostics.
- [ ] **Implement `common` steps** — apt packages, sysctl BBR, SSH hardening, firewall (UFW). Each is a `Step` with idempotency check.
- [ ] **Implement `docker` steps** — Docker CE install (skip if running), docker-compose.yml template + up.

### Agent B: Panel provisioning steps

**File ownership:** `src/meridian/provision/panel.py`, `src/meridian/provision/xray.py`

- [ ] **Implement panel setup steps** — health check, default login, change credentials, apply settings, save credentials. Each step uses `PanelClient` internally.
- [ ] **Implement inbound creation steps** — one parameterized step driven by `Protocol` registry (not one per protocol). Check if inbound exists by remark, create if not, assert success, verify Xray health.
- [ ] **Implement key generation step** — x25519 + UUID via `docker exec`, parse output, save to credentials.
- [ ] **Template rendering** — Caddy/HAProxy configs rendered via Jinja2 in Python (templates stay as `.j2` files, rendered by `jinja2.Environment`).

## Wave 4 — Migration Completion

**2 agents.** Wire the provisioner into the CLI and remove Ansible.

### Agent A: Service provisioning + uninstall

**File ownership:** `src/meridian/provision/services.py`, `src/meridian/provision/uninstall.py`

- [ ] **Implement HAProxy steps** — apt install, template config, systemctl enable + start. Idempotency: check if config matches.
- [ ] **Implement Caddy steps** — apt install, template `meridian.caddy`, add import line, deploy connection-info HTML, stats script + cron. DNS pre-check as a Step (fails fast).
- [ ] **Implement output steps** — QR generation (server-side), connection summary display (terminal). Replaces `output` role.
- [ ] **Implement uninstall provisioner** — reverse of setup steps. Replaces `playbook-uninstall.yml`.

### Agent B: CLI rewire + cleanup

**File ownership:** `src/meridian/commands/setup.py`, `src/meridian/ansible.py`, `src/meridian/cli.py`, `.github/workflows/`, `Makefile`

- [ ] **Rewire `setup.py`** — replace `run_playbook("playbook.yml", ...)` with `Provisioner(steps).run(conn, ctx)`. Keep the interactive wizard as-is.
- [ ] **Rewire `uninstall.py`** — replace `run_playbook("playbook-uninstall.yml", ...)` with uninstall provisioner.
- [ ] **Delete `ansible.py`** — `ensure_ansible()`, `ensure_collections()`, `run_playbook()`, `write_inventory()` — all gone.
- [ ] **Update CI** — remove ansible-lint, ansible-check, dry-run jobs. Add provisioner unit tests. Keep template rendering test (templates are still `.j2`).
- [ ] **Update Makefile** — remove ansible-specific targets.
- [ ] **Keep playbook files temporarily** — move to `src/meridian/playbooks-legacy/` for reference during migration. Delete after one release cycle.

## Wave 5 — UX + Docs

**2 agents.** Polish the experience now that the new engine works.

### Agent A: CLI UX

**File ownership:** `src/meridian/commands/setup.py`, `src/meridian/commands/client.py`, `src/meridian/console.py`, `src/meridian/commands/check.py`, `src/meridian/commands/diagnostics.py`

- [ ] **Rewrite wizard intro** — lead with human benefit ("Set up a private internet connection that censors can't detect"), technical details after.
- [ ] **Domain prompt yes/no gate** — replace `Domain [skip]:` with "Do you have a domain? [y/N]" then ask for domain.
- [ ] **Replace jargon in error messages** — "No Reality inbound found" → "Server is not set up yet". "Failed to list inbounds" → "Could not retrieve server configuration". Audit all `fail()` calls.
- [ ] **Add progress indication** — the provisioner (Wave 3) provides streaming step output. Ensure `meridian setup` shows real-time progress like "Installing Docker... done (3.2s)".
- [ ] **Promote `--ai` flag** — make it more visible in diagnostics output and error messages.

### Agent B: Docs + Narrative

**File ownership:** `README.md`, `docs/`, `CONTRIBUTING.md`, `docs/ai/`

- [ ] **README emotional hook** — add "What is this" paragraph before Install. Add threat model summary. Rename "Feedback" → "Troubleshooting". Add supported platforms.
- [ ] **Website section reorder** — Setup → What Happens → Connect → Technology. Add prereqs in hero. Surface Cloudflare setup.
- [ ] **Recovery flow documentation** — "IP blocked, now what?" coherent path. VPS guidance. SSH key pointer. Family sharing workflow.
- [ ] **Fix AI docs drift** — `context.md` stale "downloads playbooks" reference, removed `*-clients.yml` path. Regenerate `make ai-docs`.
- [ ] **Update architecture docs** — reflect new provisioner architecture, remove Ansible references.

## Wave 6 — Scale Features

**2 agents.** Depends on Waves 3-5.

### Agent A: Batch operations

- [ ] **Batch client add** — `meridian client add alice bob charlie` — single SSH session, multiple UUIDs.
- [ ] **Client migration for rebuilds** — detect existing clients on old server, offer to re-create on new server.

### Agent B: Multi-server

- [ ] **Cross-server `meridian status`** — all servers + client counts in one view.
- [ ] **Per-client traffic/IP limits** — `--limit-gb 100 --limit-ip 3` flags on `client add`.

---

## Icebox (long-term, not scheduled)

- [ ] Subscription URL support for client management at scale
- [ ] Key/credential rotation without full uninstall/reinstall
- [ ] Proactive IP block notification (Telegram/webhook alerts)
- [ ] Zero-to-VPN onboarding wizard on meridian.msu.rocks
- [ ] Password-protected connection info page
- [ ] Shell completion support (typer built-in)
- [ ] Pin ansible-lint via `gh_action_ref` (goes away with Ansible removal)
- [ ] Add deployed version to diagnostics (`/etc/meridian/version`)
- [ ] Add "broke after update" issue template

---

## Completed (historical)

<details>
<summary>Previously completed items</summary>

- [x] Replace `eval` with `printf -v` — code injection fix
- [x] Rewrite CLI in Python — 1,727-line bash → modular Python package
- [x] Gate CD/Release on CI success
- [x] Add `body_format` policy check in CI
- [x] Auto-discover templates in render test
- [x] Add connection-info app link sync check
- [x] Add Xray health check after inbound creation
- [x] Fix CLI server install for non-root users
- [x] Add `apt` fallback for Ansible installation
- [x] Retry Ansible collection install (3x)
- [x] Validate VERSION format in CI
- [x] Extract YAML → `ServerCredentials` dataclass
- [x] Standardize flag parsing via typer
- [x] Docker integration test for 3x-ui API
- [x] PyPI trusted publisher + registration
- [x] Consolidate connection-info HTML templates
- [x] Add mypy type checking to CI
- [x] SHA256 checksum verification for auto-update
- [x] Make shellcheck blocking in CI

</details>
