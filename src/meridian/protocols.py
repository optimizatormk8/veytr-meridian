"""Protocol/inbound type definitions — single source of truth.

Keep in sync with inbound_types in group_vars/all.yml.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InboundType:
    """Defines an inbound protocol type in 3x-ui."""

    remark: str  # 3x-ui inbound remark (e.g., "VLESS-Reality")
    email_prefix: str  # Client email prefix (e.g., "reality-")
    flow: str  # Xray flow value (e.g., "xtls-rprx-vision")
    url_scheme: str = "vless"  # URL scheme for connection strings


# Single source of truth for all inbound types.
# Ansible equivalent: inbound_types in group_vars/all.yml
INBOUND_TYPES: dict[str, InboundType] = {
    "reality": InboundType(
        remark="VLESS-Reality",
        email_prefix="reality-",
        flow="xtls-rprx-vision",
    ),
    "wss": InboundType(
        remark="VLESS-WSS",
        email_prefix="wss-",
        flow="",
    ),
    "xhttp": InboundType(
        remark="VLESS-Reality-XHTTP",
        email_prefix="xhttp-",
        flow="",
    ),
}
