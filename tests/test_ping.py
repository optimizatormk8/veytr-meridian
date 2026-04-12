"""Tests for meridian test (ping) reachability helpers."""

from __future__ import annotations

import pytest

from meridian.commands.ping import _domain_https_reachable


@pytest.mark.parametrize(
    ("http_code", "expected"),
    [
        ("200", True),
        ("301", True),
        ("403", True),
        ("404", True),
        ("000", False),
        ("", False),
        ("  ", False),
        ("500", False),
        ("418", False),
    ],
)
def test_domain_https_reachable(http_code: str, expected: bool) -> None:
    assert _domain_https_reachable(http_code) is expected
