"""Client management -- add, list, remove proxy clients."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from meridian.commands.resolve import (
    ensure_server_connection,
    fetch_credentials,
    resolve_server,
)
from meridian.config import SERVERS_FILE
from meridian.console import err_console, fail, info, ok, warn
from meridian.credentials import ClientEntry, ServerCredentials
from meridian.output import (
    build_vless_urls,
    print_terminal_output,
    save_connection_html,
    save_connection_text,
)
from meridian.panel import Inbound, PanelClient, PanelError
from meridian.protocols import INBOUND_TYPES
from meridian.servers import ServerRegistry

# -- Helpers --


def _validate_client_name(name: str) -> None:
    """Validate client name format. Exits on invalid."""
    if not name:
        fail("Client name is required", hint="Usage: meridian client add NAME")
    if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$", name):
        fail(
            f"Client name '{name}' is invalid",
            hint="Use letters, numbers, hyphens, and underscores.",
        )


def _load_creds(creds_dir: Path) -> ServerCredentials:
    """Load and validate credentials from creds_dir."""
    proxy_file = creds_dir / "proxy.yml"
    if not proxy_file.exists():
        fail("No credentials found", hint="Deploy the server first: meridian setup")

    creds = ServerCredentials.load(proxy_file)
    if not creds.has_credentials:
        fail("No panel credentials found", hint="Deploy the server first: meridian setup")
    return creds


def _make_panel(creds: ServerCredentials, conn: object) -> PanelClient:
    """Create and authenticate a PanelClient."""
    from meridian.ssh import ServerConnection

    assert isinstance(conn, ServerConnection)
    panel = PanelClient(
        conn=conn,
        panel_port=creds.panel.port,
        web_base_path=creds.panel.web_base_path or "",
    )
    try:
        panel.login(creds.panel.username or "", creds.panel.password or "")
    except PanelError as e:
        fail(f"Panel login failed: {e}", hint="Check credentials or run: meridian setup")
    return panel


def _sync_credentials_to_server(resolved: object) -> None:
    """Sync local credentials back to the server's /etc/meridian/."""
    from meridian.commands.resolve import ResolvedServer

    assert isinstance(resolved, ResolvedServer)
    if resolved.local_mode:
        return  # Already on the server

    # SCP the credentials directory to the server
    import subprocess

    try:
        subprocess.run(
            [
                "scp",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=5",
                "-o",
                "StrictHostKeyChecking=accept-new",
                "-r",
                f"{resolved.creds_dir}/",
                f"{resolved.user}@{resolved.ip}:/etc/meridian/",
            ],
            capture_output=True,
            text=True,
            timeout=15,
            stdin=subprocess.DEVNULL,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        warn("Could not sync credentials to server")


# -- Client Add --


def run_add(
    name: str,
    user: str = "root",
    requested_server: str = "",
) -> None:
    """Add a new client to the proxy server via direct panel API calls."""
    _validate_client_name(name)

    registry = ServerRegistry(SERVERS_FILE)
    resolved = resolve_server(registry, requested_server=requested_server, user=user)
    resolved = ensure_server_connection(resolved)
    fetch_credentials(resolved)

    creds = _load_creds(resolved.creds_dir)
    info(f"Adding client '{name}'...")

    # Check for duplicates in credentials
    if any(c.name == name for c in creds.clients):
        fail(f"Client '{name}' already exists", hint="Use: meridian client list")

    # Connect to panel
    panel = _make_panel(creds, resolved.conn)
    try:
        # List inbounds and find active ones
        try:
            inbounds = panel.list_inbounds()
        except PanelError as e:
            fail(f"Failed to list inbounds: {e}")

        # Check for duplicate in Reality inbound (canonical)
        reality_type = INBOUND_TYPES["reality"]
        reality_inbound = None
        for ib in inbounds:
            if ib.remark == reality_type.remark:
                reality_inbound = ib
                break

        if reality_inbound is None:
            fail(
                "No Reality inbound found on the server",
                hint="Make sure the server is set up first: meridian setup",
            )

        # Check if client already exists in the panel (by email)
        for client in reality_inbound.clients:
            if client.get("email") == f"{reality_type.email_prefix}{name}":
                fail(f"Client '{name}' already exists on the panel", hint="Use: meridian client list")

        # Generate UUIDs
        try:
            reality_uuid = panel.generate_uuid()
        except PanelError as e:
            fail(f"Failed to generate UUID: {e}")

        # WSS UUID only if domain mode with WSS inbound
        wss_uuid = ""
        wss_type = INBOUND_TYPES["wss"]
        wss_inbound = None
        for ib in inbounds:
            if ib.remark == wss_type.remark:
                wss_inbound = ib
                break

        if wss_inbound:
            try:
                wss_uuid = panel.generate_uuid()
            except PanelError as e:
                fail(f"Failed to generate WSS UUID: {e}")

        # Find XHTTP inbound
        xhttp_type = INBOUND_TYPES["xhttp"]
        xhttp_inbound = None
        xhttp_port = 0
        for ib in inbounds:
            if ib.remark == xhttp_type.remark:
                xhttp_inbound = ib
                xhttp_port = ib.port
                break

        # Add client to each active inbound
        # Build the inbound map: (inbound, uuid, type_key)
        active_inbounds: list[tuple[object, str, str]] = []
        active_inbounds.append((reality_inbound, reality_uuid, "reality"))
        if xhttp_inbound:
            active_inbounds.append((xhttp_inbound, reality_uuid, "xhttp"))
        if wss_inbound:
            active_inbounds.append((wss_inbound, wss_uuid, "wss"))

        for ib, uuid, type_key in active_inbounds:
            itype = INBOUND_TYPES[type_key]
            client_settings = {
                "clients": [
                    {
                        "id": uuid,
                        "flow": itype.flow,
                        "email": f"{itype.email_prefix}{name}",
                        "limitIp": 2,
                        "totalGB": 0,
                        "expiryTime": 0,
                        "enable": True,
                        "tgId": "",
                        "subId": "",
                        "reset": 0,
                    }
                ]
            }
            try:
                panel.add_client(ib.id, client_settings)
            except PanelError as e:
                fail(f"Failed to add client to {itype.remark}: {e}")

        ok(f"Client '{name}' added to panel")

        # Update credentials file
        creds.clients.append(
            ClientEntry(
                name=name,
                added=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                reality_uuid=reality_uuid,
                wss_uuid=wss_uuid,
            )
        )
        creds.save(resolved.creds_dir / "proxy.yml")

        # Generate output files
        urls = build_vless_urls(
            name=name,
            reality_uuid=reality_uuid,
            wss_uuid=wss_uuid,
            creds=creds,
            xhttp_port=xhttp_port,
        )

        server_ip = creds.server.ip or resolved.ip
        file_prefix = f"{resolved.ip}-{name}"
        save_connection_text(
            urls,
            resolved.creds_dir / f"{file_prefix}-connection-info.txt",
            server_ip,
        )
        save_connection_html(
            urls,
            resolved.creds_dir / f"{file_prefix}-connection-info.html",
            server_ip,
            domain=creds.server.domain or "",
        )

        # Sync credentials to server
        _sync_credentials_to_server(resolved)

        # Print terminal output
        print_terminal_output(urls, resolved.creds_dir, server_ip)

        err_console.print(f"  [dim]Test reachability: meridian ping {resolved.ip}[/dim]")
        err_console.print("  [dim]View all clients:  meridian client list[/dim]\n")

    finally:
        panel.cleanup()


# -- Client List --


def run_list(
    user: str = "root",
    requested_server: str = "",
) -> None:
    """List all clients via direct panel API query (no Ansible)."""
    registry = ServerRegistry(SERVERS_FILE)
    resolved = resolve_server(registry, requested_server=requested_server, user=user)

    resolved = ensure_server_connection(resolved)
    fetch_credentials(resolved)

    creds = _load_creds(resolved.creds_dir)
    panel = _make_panel(creds, resolved.conn)
    try:
        try:
            inbounds = panel.list_inbounds()
        except PanelError as e:
            fail(f"Failed to list inbounds: {e}")

        _display_client_list_from_inbounds(inbounds)
    finally:
        panel.cleanup()


# -- Client Remove --


def run_remove(
    name: str,
    user: str = "root",
    requested_server: str = "",
) -> None:
    """Remove a client from the proxy server via direct panel API calls."""
    _validate_client_name(name)

    registry = ServerRegistry(SERVERS_FILE)
    resolved = resolve_server(registry, requested_server=requested_server, user=user)
    resolved = ensure_server_connection(resolved)
    fetch_credentials(resolved)

    creds = _load_creds(resolved.creds_dir)
    info(f"Removing client '{name}'...")

    panel = _make_panel(creds, resolved.conn)
    try:
        try:
            inbounds = panel.list_inbounds()
        except PanelError as e:
            fail(f"Failed to list inbounds: {e}")

        # Verify client exists in Reality inbound (canonical)
        reality_type = INBOUND_TYPES["reality"]
        reality_inbound = None
        for ib in inbounds:
            if ib.remark == reality_type.remark:
                reality_inbound = ib
                break

        if reality_inbound is None:
            fail("No Reality inbound found on the server")

        # Find client by email in Reality inbound
        client_email = f"{reality_type.email_prefix}{name}"
        client_found = False
        for client in reality_inbound.clients:
            if client.get("email") == client_email:
                client_found = True
                break

        if not client_found:
            fail(f"Client '{name}' not found", hint="Check client name with: meridian client list")

        # Remove from each active inbound
        for type_key, itype in INBOUND_TYPES.items():
            email = f"{itype.email_prefix}{name}"
            for ib in inbounds:
                if ib.remark != itype.remark:
                    continue
                # Find client UUID by email
                for client in ib.clients:
                    if client.get("email") == email:
                        client_uuid = client.get("id", "")
                        if client_uuid:
                            try:
                                panel.remove_client(ib.id, client_uuid)
                            except PanelError as e:
                                warn(f"Failed to remove from {itype.remark}: {e}")

        ok(f"Client '{name}' removed from panel")

        # Update credentials file
        creds.clients = [c for c in creds.clients if c.name != name]
        creds.save(resolved.creds_dir / "proxy.yml")

        # Delete local output files
        for pattern in [
            f"*-{name}-connection-info.html",
            f"*-{name}-connection-info.txt",
        ]:
            for f in resolved.creds_dir.glob(pattern):
                f.unlink(missing_ok=True)

        # Sync credentials to server
        _sync_credentials_to_server(resolved)

        err_console.print(f"\n  Client '{name}' has been removed from all active inbounds.\n")

    finally:
        panel.cleanup()


# -- Display --


def _display_client_list_from_inbounds(inbounds: list[Inbound]) -> None:
    """Display client list from parsed Inbound objects."""
    from rich.table import Table

    # Build lookup: remark -> set of client emails
    clients_by_remark: dict[str, set[str]] = {}
    for ib in inbounds:
        emails = {c.get("email", "") for c in ib.clients}
        clients_by_remark[ib.remark] = emails

    # Reality is the canonical inbound
    reality_type = INBOUND_TYPES["reality"]
    reality_clients: list[dict] = []
    for ib in inbounds:
        if ib.remark == reality_type.remark:
            reality_clients = ib.clients
            break

    # Build email sets for non-canonical inbound types
    other_types = {
        key: clients_by_remark.get(itype.remark, set()) for key, itype in INBOUND_TYPES.items() if key != "reality"
    }

    table = Table(title="Proxy Clients", show_lines=False, pad_edge=False, box=None, padding=(0, 2))
    table.add_column("Name", style="bold")
    table.add_column("Status")
    table.add_column("Protocols")

    for c in reality_clients:
        email = c.get("email", "")
        name = email.removeprefix(reality_type.email_prefix) if email.startswith(reality_type.email_prefix) else email
        status = "[green]active[/green]" if c.get("enable", True) else "[dim]disabled[/dim]"
        protos = ["Reality"]
        for key, itype in INBOUND_TYPES.items():
            if key == "reality":
                continue
            if f"{itype.email_prefix}{name}" in other_types[key]:
                protos.append(key.upper())
        table.add_row(name, status, " + ".join(protos))

    count = len(reality_clients)
    suffix = "s" if count != 1 else ""

    err_console.print()
    err_console.print(table)
    err_console.print()
    err_console.print(f"  [dim]Total: {count} client{suffix}[/dim]")
    err_console.print()
    err_console.print("  [dim]Add: meridian client add NAME  |  Remove: meridian client remove NAME[/dim]")
    err_console.print()
