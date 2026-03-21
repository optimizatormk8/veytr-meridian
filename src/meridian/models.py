"""Shared data models used across meridian modules.

Centralizes dataclasses that would otherwise create circular imports
between panel.py, protocols.py, and output.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Inbound:
    """An inbound from the 3x-ui panel."""

    id: int
    remark: str
    protocol: str
    port: int
    clients: list[dict] = field(default_factory=list)
    stream_settings: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ProtocolURL:
    """A connection URL for a specific protocol.

    Used by output generation to iterate protocols generically
    instead of hardcoding reality/xhttp/wss fields.
    """

    key: str  # Protocol key: "reality", "xhttp", "wss"
    label: str  # Human-readable label: "Primary", "XHTTP", "CDN Backup"
    url: str  # Full connection URL (e.g., vless://...)
