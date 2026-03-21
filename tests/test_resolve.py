"""Tests for server resolution logic — all 5+ resolution paths."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
import typer

from meridian.commands.resolve import resolve_and_connect, resolve_server
from meridian.config import CREDS_BASE, SERVER_CREDS_DIR
from meridian.servers import ServerEntry, ServerRegistry


class TestExplicitIP:
    """Path 1: explicit_ip argument takes highest priority."""

    def test_explicit_ip_returns_resolved(self, servers_file: Path) -> None:
        reg = ServerRegistry(servers_file)
        result = resolve_server(reg, explicit_ip="1.2.3.4")
        assert result.ip == "1.2.3.4"
        assert result.user == "root"  # default
        assert result.local_mode is False

    def test_explicit_ip_with_user(self, servers_file: Path) -> None:
        reg = ServerRegistry(servers_file)
        result = resolve_server(reg, explicit_ip="1.2.3.4", user="ubuntu")
        assert result.user == "ubuntu"

    def test_explicit_ip_picks_user_from_registry(self, servers_file: Path) -> None:
        reg = ServerRegistry(servers_file)
        reg.add(ServerEntry("1.2.3.4", "ubuntu", "mybox"))
        result = resolve_server(reg, explicit_ip="1.2.3.4")
        assert result.user == "ubuntu"  # resolved from registry

    def test_explicit_user_overrides_registry(self, servers_file: Path) -> None:
        reg = ServerRegistry(servers_file)
        reg.add(ServerEntry("1.2.3.4", "ubuntu", "mybox"))
        result = resolve_server(reg, explicit_ip="1.2.3.4", user="admin")
        assert result.user == "admin"  # explicit overrides

    def test_explicit_ip_creds_dir(self, tmp_home: Path, servers_file: Path) -> None:
        reg = ServerRegistry(servers_file)
        result = resolve_server(reg, explicit_ip="5.6.7.8")
        assert result.creds_dir == CREDS_BASE / "5.6.7.8"


class TestServerFlag:
    """Path 2: --server flag (by name or IP)."""

    def test_server_by_name(self, servers_file: Path) -> None:
        reg = ServerRegistry(servers_file)
        reg.add(ServerEntry("1.2.3.4", "root", "mybox"))
        result = resolve_server(reg, requested_server="mybox")
        assert result.ip == "1.2.3.4"
        assert result.user == "root"

    def test_server_by_ip(self, servers_file: Path) -> None:
        reg = ServerRegistry(servers_file)
        reg.add(ServerEntry("1.2.3.4", "ubuntu", "mybox"))
        result = resolve_server(reg, requested_server="1.2.3.4")
        assert result.ip == "1.2.3.4"
        assert result.user == "ubuntu"

    def test_server_ip_not_in_registry(self, servers_file: Path) -> None:
        """Bare IP via --server should still resolve even if not registered."""
        reg = ServerRegistry(servers_file)
        result = resolve_server(reg, requested_server="9.8.7.6")
        assert result.ip == "9.8.7.6"
        assert result.user == "root"

    def test_server_name_not_found_exits(self, servers_file: Path) -> None:
        reg = ServerRegistry(servers_file)
        with pytest.raises(typer.Exit) as exc_info:
            resolve_server(reg, requested_server="nonexistent")
        assert exc_info.value.exit_code == 1

    def test_server_by_name_inherits_user(self, servers_file: Path) -> None:
        reg = ServerRegistry(servers_file)
        reg.add(ServerEntry("1.2.3.4", "deploy", "prod"))
        result = resolve_server(reg, requested_server="prod")
        assert result.user == "deploy"


class TestSingleServerAutoSelect:
    """Path 4: single registered server auto-selected."""

    def test_single_server_auto_select(self, servers_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Patch _detect_local_mode_from_creds to return None (not on server)
        monkeypatch.setattr(
            "meridian.commands.resolve._detect_local_mode_from_creds",
            lambda: None,
        )
        reg = ServerRegistry(servers_file)
        reg.add(ServerEntry("10.20.30.40", "root", "only-one"))
        result = resolve_server(reg)
        assert result.ip == "10.20.30.40"
        assert result.user == "root"


class TestMultipleServers:
    """Path 5: multiple servers registered, no selection."""

    def test_multiple_servers_fail(self, servers_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "meridian.commands.resolve._detect_local_mode_from_creds",
            lambda: None,
        )
        reg = ServerRegistry(servers_file)
        reg.add(ServerEntry("1.2.3.4", "root", "server1"))
        reg.add(ServerEntry("5.6.7.8", "root", "server2"))
        with pytest.raises(typer.Exit) as exc_info:
            resolve_server(reg)
        assert exc_info.value.exit_code == 1


class TestNoServers:
    """Path 6: empty registry, no explicit IP."""

    def test_no_servers_fail(self, servers_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "meridian.commands.resolve._detect_local_mode_from_creds",
            lambda: None,
        )
        reg = ServerRegistry(servers_file)
        with pytest.raises(typer.Exit) as exc_info:
            resolve_server(reg)
        assert exc_info.value.exit_code == 1


class TestLocalMode:
    """Path 3: running on the server itself as root."""

    def test_local_mode_detection(self, servers_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "meridian.commands.resolve._detect_local_mode_from_creds",
            lambda: "10.0.0.1",
        )
        reg = ServerRegistry(servers_file)
        result = resolve_server(reg)
        assert result.ip == "10.0.0.1"
        assert result.local_mode is True
        assert result.creds_dir == SERVER_CREDS_DIR


class TestResolvedServer:
    """Test ResolvedServer dataclass properties."""

    def test_frozen(self, servers_file: Path) -> None:
        reg = ServerRegistry(servers_file)
        result = resolve_server(reg, explicit_ip="1.2.3.4")
        with pytest.raises(AttributeError):
            result.ip = "changed"  # type: ignore[misc]

    def test_conn_created(self, servers_file: Path) -> None:
        reg = ServerRegistry(servers_file)
        result = resolve_server(reg, explicit_ip="1.2.3.4", user="ubuntu")
        assert result.conn.ip == "1.2.3.4"
        assert result.conn.user == "ubuntu"
        assert result.conn.local_mode is False


class TestResolveAndConnect:
    """Tests for the resolve_and_connect() convenience wrapper."""

    def test_chains_all_three_steps(self, servers_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """resolve_and_connect chains resolve, ensure_connection, fetch_creds."""
        import meridian.commands.resolve as resolve_mod

        mock_resolved = MagicMock()
        mock_resolved.ip = "1.2.3.4"

        resolve_calls: list[str] = []

        def fake_resolve(registry, explicit_ip="", requested_server="", user=""):
            resolve_calls.append("resolve")
            return mock_resolved

        def fake_ensure(resolved):
            resolve_calls.append("ensure")
            return resolved

        def fake_fetch(resolved):
            resolve_calls.append("fetch")
            return True

        monkeypatch.setattr(resolve_mod, "ServerRegistry", lambda path: MagicMock())
        monkeypatch.setattr(resolve_mod, "resolve_server", fake_resolve)
        monkeypatch.setattr(resolve_mod, "ensure_server_connection", fake_ensure)
        monkeypatch.setattr(resolve_mod, "fetch_credentials", fake_fetch)

        result = resolve_and_connect(ip="1.2.3.4")

        assert resolve_calls == ["resolve", "ensure", "fetch"]
        assert result is mock_resolved

    def test_skip_ssh_check(self, servers_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """check_ssh=False skips ensure_server_connection."""
        import meridian.commands.resolve as resolve_mod

        mock_resolved = MagicMock()
        ensure_called = []

        monkeypatch.setattr(resolve_mod, "ServerRegistry", lambda path: MagicMock())
        monkeypatch.setattr(resolve_mod, "resolve_server", lambda *a, **kw: mock_resolved)
        monkeypatch.setattr(resolve_mod, "ensure_server_connection", lambda r: ensure_called.append(r) or r)
        monkeypatch.setattr(resolve_mod, "fetch_credentials", lambda r: True)

        resolve_and_connect(ip="1.2.3.4", check_ssh=False)

        assert ensure_called == [], "ensure_server_connection should not be called when check_ssh=False"

    def test_skip_fetch_creds(self, servers_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """fetch_creds=False skips fetch_credentials."""
        import meridian.commands.resolve as resolve_mod

        mock_resolved = MagicMock()
        fetch_called = []

        monkeypatch.setattr(resolve_mod, "ServerRegistry", lambda path: MagicMock())
        monkeypatch.setattr(resolve_mod, "resolve_server", lambda *a, **kw: mock_resolved)
        monkeypatch.setattr(resolve_mod, "ensure_server_connection", lambda r: r)
        monkeypatch.setattr(resolve_mod, "fetch_credentials", lambda r: fetch_called.append(r) or True)

        resolve_and_connect(ip="1.2.3.4", fetch_creds=False)

        assert fetch_called == [], "fetch_credentials should not be called when fetch_creds=False"

    def test_passes_requested_server(self, servers_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """requested_server is forwarded to resolve_server correctly."""
        import meridian.commands.resolve as resolve_mod

        captured: dict[str, str] = {}

        def fake_resolve(registry, explicit_ip="", requested_server="", user=""):
            captured["requested_server"] = requested_server
            captured["user"] = user
            return MagicMock()

        monkeypatch.setattr(resolve_mod, "ServerRegistry", lambda path: MagicMock())
        monkeypatch.setattr(resolve_mod, "resolve_server", fake_resolve)
        monkeypatch.setattr(resolve_mod, "ensure_server_connection", lambda r: r)
        monkeypatch.setattr(resolve_mod, "fetch_credentials", lambda r: True)

        resolve_and_connect(requested_server="mybox", user="ubuntu")

        assert captured["requested_server"] == "mybox"
        assert captured["user"] == "ubuntu"
