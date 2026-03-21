"""Tests for protocol/inbound type registry."""

from __future__ import annotations

from meridian.protocols import INBOUND_TYPES, InboundType


class TestInboundTypes:
    def test_all_types_present(self) -> None:
        assert set(INBOUND_TYPES.keys()) == {"reality", "wss", "xhttp"}

    def test_type_is_frozen_dataclass(self) -> None:
        for t in INBOUND_TYPES.values():
            assert isinstance(t, InboundType)

    def test_reality_values(self) -> None:
        r = INBOUND_TYPES["reality"]
        assert r.remark == "VLESS-Reality"
        assert r.email_prefix == "reality-"
        assert r.flow == "xtls-rprx-vision"
        assert r.url_scheme == "vless"

    def test_wss_values(self) -> None:
        w = INBOUND_TYPES["wss"]
        assert w.remark == "VLESS-WSS"
        assert w.email_prefix == "wss-"
        assert w.flow == ""

    def test_xhttp_values(self) -> None:
        x = INBOUND_TYPES["xhttp"]
        assert x.remark == "VLESS-Reality-XHTTP"
        assert x.email_prefix == "xhttp-"
        assert x.flow == ""

    def test_email_prefixes_unique(self) -> None:
        prefixes = [t.email_prefix for t in INBOUND_TYPES.values()]
        assert len(prefixes) == len(set(prefixes))

    def test_remarks_unique(self) -> None:
        remarks = [t.remark for t in INBOUND_TYPES.values()]
        assert len(remarks) == len(set(remarks))
