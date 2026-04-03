# commands — One module per subcommand

## Design decisions

**One file per command** — keeps concerns isolated. Each is a Typer sub-app registered in `cli.py`.

**Server resolution cascade** in `resolve.py` — strict priority order ensures predictable behavior:
1. Explicit IP → 2. `--server` name → 3. `local` keyword → 4. Single-server auto-select → 5. Multi-server prompt → 6. Fail with hint

**Three-step pattern**: resolve → ensure connection → fetch credentials. Every server-touching command follows this. Deviating causes subtle bugs.

**Version mismatch check** — `fetch_credentials()` compares `deployed_with` against running CLI. Warns once per server per session. Non-blocking.

**Wizard UX conventions** — the deploy wizard uses `console.py` helpers exclusively:
- **`choose()`** for any decision with 2+ options. Never raw Y/n prompts. Shows numbered list, user picks a number. Default is always 1.
- **`prompt()`** for free-text input (IP address, domain, server name). Show defaults in brackets.
- **`confirm()`** only for the final deploy confirmation. One per command, at the end.
- **Section pattern**: bold header → dim description → blank line → `choose()`/`prompt()`.
- **`rich.status.Status`** spinner for any operation >5 seconds (scan, download). Same style as provisioner steps.
- **Summary Panel** before deploy: show all chosen settings so user can review before confirming.

## What's done well

- **`local` keyword everywhere** — `deploy local`, `check local`, `--server local` all work. Case-insensitive. Same code path.
- **Credential sync** — modify locally first, SCP back to server. No lockout on network failure.

## Pitfalls

- **Local mode has two entry points** — `local` keyword and root auto-detect. They converge on `local_mode=True` but differ on `creds_dir`.
- **SCP sync is fire-and-forget** — if SCP fails, server and local creds diverge silently.
- **`console.fail()` always exits** — raises `typer.Exit(1)`. Only call from command entry points, never library code.
- **`dev` subcommand is hidden** — not shown in `--help`. Intentional — developer tools only.
