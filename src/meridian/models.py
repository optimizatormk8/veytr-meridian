"""Shared data models for connection output."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProtocolURL:
    """A VLESS connection URL for a single protocol."""

    key: str    # "reality", "xhttp", "wss"
    label: str  # "Primary", "XHTTP", "CDN Backup"
    url: str    # Full VLESS URL (empty string if protocol not active)
