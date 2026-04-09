"""URL building and QR code generation for VLESS connections."""

from __future__ import annotations

import base64
import io

import segno

from meridian.credentials import ServerCredentials
from meridian.models import ProtocolURL, RelayURLSet
from meridian.protocols import PROTOCOLS


def build_protocol_urls(
    name: str,
    reality_uuid: str,
    wss_uuid: str,
    creds: ServerCredentials,
    server_name: str = "",
) -> list[ProtocolURL]:
    """Build VLESS connection URLs for a client across all active protocols.

    Iterates over ``PROTOCOLS`` in registry order and produces a
    ``ProtocolURL`` for every protocol whose URL can be built given the
    supplied arguments.  Protocols that are not active (e.g. WSS without a
    domain, XHTTP without a path) are omitted from the returned list.

    Args:
        name: Client display name (used in URL fragment).
        reality_uuid: UUID for Reality and XHTTP connections.
        wss_uuid: UUID for WSS connection (empty if not domain mode).
        creds: Server credentials with protocol configs.

    Returns:
        Ordered list of ``ProtocolURL`` objects, one per active protocol.
    """
    result: list[ProtocolURL] = []
    for proto in PROTOCOLS.values():
        url = proto.build_url_from_creds(reality_uuid, wss_uuid, creds, name, server_name=server_name)
        if url:
            result.append(ProtocolURL(key=proto.key, label=proto.display_label, url=url))
    return result


def build_relay_urls(
    name: str,
    reality_uuid: str,
    wss_uuid: str,
    creds: ServerCredentials,
    relay_ip: str,
    relay_name: str = "",
    relay_port: int = 443,
    server_name: str = "",
    relay_sni: str = "",
) -> RelayURLSet:
    """Build connection URLs that route through a relay node.

    A dumb L4 relay forwards TCP transparently, so TLS goes end-to-end
    to the exit server.  All protocols work if we set explicit ``sni=``
    parameters pointing to the exit's TLS certificate identity:

    - **Reality**: uses relay-specific SNI when available (per-relay
      Xray inbound on exit handles it). Falls back to exit's SNI.
    - **XHTTP**: add ``sni=<exit_ip_or_domain>`` so nginx's cert matches.
    - **WSS**: add ``sni=<domain>`` + ``host=<domain>`` (domain mode only).

    Args:
        name: Client display name.
        reality_uuid: UUID for Reality and XHTTP connections.
        wss_uuid: UUID for WSS connection (empty if not domain mode).
        creds: Exit server credentials (SNI, keys, paths).
        relay_ip: Relay node IP address (substituted for exit IP).
        relay_name: Friendly relay name (used in URL fragment).
        relay_port: Relay listen port (default 443).
        relay_sni: Relay-specific SNI for Reality (empty = use exit's SNI).

    Returns:
        A ``RelayURLSet`` with all active protocol URLs via this relay.
    """
    relay_label = relay_name or relay_ip
    urls: list[ProtocolURL] = []

    for proto in PROTOCOLS.values():
        url = proto.build_relay_url(
            reality_uuid,
            wss_uuid,
            creds,
            name,
            relay_ip,
            relay_port,
            relay_sni=relay_sni,
            relay_name=relay_name,
            server_name=server_name,
        )
        if url:
            label = f"{proto.display_label} (via {relay_label})"
            urls.append(ProtocolURL(key=proto.key, label=label, url=url))

    return RelayURLSet(relay_ip=relay_ip, relay_name=relay_name, urls=urls)


def build_all_relay_urls(
    name: str,
    reality_uuid: str,
    wss_uuid: str,
    creds: ServerCredentials,
    server_name: str = "",
) -> list[RelayURLSet]:
    """Build relay URL sets for all relays attached to the exit server.

    Returns an empty list if no relays are configured.
    """
    return [
        build_relay_urls(
            name,
            reality_uuid,
            wss_uuid,
            creds,
            relay.ip,
            relay.name,
            relay.port,
            server_name=server_name,
            relay_sni=relay.sni,
        )
        for relay in creds.relays
    ]


def generate_qr_terminal(url: str) -> str:
    """Generate a QR code for terminal display."""
    try:
        qr = segno.make(url)
        buf = io.StringIO()
        qr.terminal(out=buf, compact=True)
        return buf.getvalue()
    except (ValueError, OSError):
        return ""


def generate_qr_base64(url: str) -> str:
    """Generate a QR code as base64-encoded PNG for HTML embedding."""
    try:
        qr = segno.make(url)
        buf = io.BytesIO()
        qr.save(buf, kind="png", scale=12)
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except (ValueError, OSError):
        return ""
