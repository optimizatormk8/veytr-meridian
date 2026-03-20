# Backlog

**Last updated:** 2026-03-20
**Version:** 1.2.5

---

## P0 — Critical (done)

- [x] Replace `eval` with `printf -v` in `prompt()` to prevent code injection
- [x] Add SHA256 checksum verification to auto-update
- [x] Make shellcheck blocking in CI (was `|| true`, no-op)
- [x] Fix auto-update downgrade when running dev version (semver direction check)
- [x] Fix `eval` injection vector in `prompt()` function

## P1 — High (done)

- [x] Gate CD and Release workflows on CI success (`workflow_run` chain)
- [x] Add `body_format` policy check in CI (prevent form-urlencoded on inbound/client APIs)
- [x] Auto-discover templates in render test (was manual list, missed `update-stats.py.j2`)
- [x] Add connection-info app link sync check in CI
- [x] Add Xray health check after inbound creation (catch crash loops)
- [x] Fix CLI server install for non-root users (sudo mv fallback)
- [x] Suggest `meridian uninstall` + retry on inbound creation failures
- [x] Add `apt` fallback for Ansible installation (WSL compat)
- [x] Retry Ansible collection install up to 3 times (flaky networks)

## P1 — High (open)

- [ ] Pin ansible-lint via `gh_action_ref: "v25.5.0"` — `@main` is upstream-recommended but a breaking change could randomly fail CI
- [ ] Add `ansible.cfg` validation to CI — verify `jinja2_native = True` exists (critical for `body_format: json` integer typing)
- [ ] Validate VERSION format in CI — ensure `^\d+\.\d+\.\d+$` (malformed version breaks release + auto-update)
- [ ] Add checksum verification to `install.sh` — same SHA256 check as auto-update, for fresh installs via `curl | bash`
- [ ] Add Docker integration test for 3x-ui API — spin up 3x-ui in CI, run login/create-inbound/list/verify JSON round-trip (would have caught the form-urlencoded corruption bug)

## P2 — Medium (open)

- [ ] Extract `yaml_get()` helper in meridian CLI — 10+ instances of `grep '^field:' | awk '{print $2}' | tr -d '"'` for YAML parsing; fragile, breaks on spaces/special chars
- [ ] Standardize `parse_flags()` across commands — 8 duplicate `while/case` flag-parsing blocks; extract shared `--user`, `--server`, `--yes` handling
- [ ] Add deployed playbook version to diagnostics — write VERSION to `/etc/meridian/version` during deploy, read in `meridian diagnostics` to catch version mismatch
- [ ] Consolidate 3 connection-info HTML templates into one — biggest drift risk; use `{% if domain_mode %}` / `{% if relay_mode %}` conditionals instead of 3 copies
- [ ] Add "broke after update" issue template — capture old version, new version, timing, auto-update vs manual
- [ ] Improve dry-run CI job — remove `|| echo` suppression, use `--tags` for local-compatible tasks, add domain mode and chain mode dry-runs
- [ ] Add credential schema validation test — render credential template with mocks, verify the resulting YAML can be parsed by CLI's grep/awk commands

## P3 — Low (open)

- [ ] Add VERSION semver validation in release workflow (not just CI)
- [ ] Replace `MockUndefined` in template tests with stricter undefined handling — currently silently renders undefined vars as empty string
- [ ] Add HTML validation for rendered connection-info templates
- [ ] Add docs/ drift detection in CI — verify `docs/` copies match source files (currently only CD sync keeps them aligned)
- [ ] Add lightweight opt-in telemetry — anonymous ping on setup success (version, OS, mode) for usage analytics

## Future — Architecture (open)

- [ ] Rewrite CLI in Python when script exceeds ~2500 lines — current 1709 lines is at the ceiling for bash maintainability; Python unlocks pytest, argparse, proper JSON/YAML handling
- [ ] If staying in bash: do NOT split into source'd modules (breaks single-file curl|bash distribution)
- [ ] Consider Python zipapp for single-file distribution if rewriting
- [ ] Proactive IP block notification — scheduled reachability check with Telegram/webhook alerts
- [ ] Self-steal mode — Reality masquerades as your own domain
- [ ] Zero-to-VPN onboarding wizard on meridian.msu.rocks
- [ ] Password-protected connection info page for family sharing
- [ ] No key/credential rotation mechanism — currently: uninstall then reinstall
