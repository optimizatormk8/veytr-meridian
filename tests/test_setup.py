"""Tests for setup wizard — detect_public_ip and run() entry points."""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import typer

from meridian.commands.resolve import detect_public_ip
from meridian.commands.setup import _print_success, _regenerate_connection_pages_after_deploy, run
from meridian.config import is_ipv4
from meridian.credentials import ClientEntry, ServerCredentials


class TestDetectPublicIP:
    def test_returns_valid_ip(self) -> None:
        mock_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="93.184.216.34\n", stderr="")
        with patch("meridian.commands.resolve.subprocess.run", return_value=mock_result):
            ip = detect_public_ip()
        assert ip == "93.184.216.34"
        assert is_ipv4(ip)

    def test_returns_empty_on_timeout(self) -> None:
        with patch(
            "meridian.commands.resolve.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="curl", timeout=5),
        ):
            ip = detect_public_ip()
        assert ip == ""

    def test_returns_empty_on_not_found(self) -> None:
        with patch(
            "meridian.commands.resolve.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            ip = detect_public_ip()
        assert ip == ""

    def test_returns_empty_on_invalid_output(self) -> None:
        mock_result = subprocess.CompletedProcess(args=[], returncode=0, stdout="not-an-ip\n", stderr="")
        with patch("meridian.commands.resolve.subprocess.run", return_value=mock_result):
            ip = detect_public_ip()
        assert ip == ""

    def test_returns_empty_on_curl_failure(self) -> None:
        mock_result = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="error")
        with patch("meridian.commands.resolve.subprocess.run", return_value=mock_result):
            ip = detect_public_ip()
        assert ip == ""

    def test_tries_fallback_url(self) -> None:
        """If first URL fails, should try the fallback."""
        calls = []

        def side_effect(*args, **kwargs):  # noqa: ANN002, ANN003, ANN202
            calls.append(args)
            # First call fails, second succeeds
            if len(calls) == 1:
                return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="")
            return subprocess.CompletedProcess(args=[], returncode=0, stdout="10.0.0.1\n", stderr="")

        with patch("meridian.commands.resolve.subprocess.run", side_effect=side_effect):
            ip = detect_public_ip()
        assert ip == "10.0.0.1"
        assert len(calls) == 2


class TestRunWithExplicitIP:
    """Test run() behavior when IP is provided explicitly (non-interactive)."""

    def test_invalid_ip_exits(self) -> None:
        """run() with invalid IP should fail."""
        with pytest.raises(typer.Exit):
            run(ip="not-an-ip", yes=True)

    def test_both_ip_and_server_flag_fails(self, tmp_home: Path) -> None:
        """Cannot use both positional IP and --server flag."""
        with pytest.raises(typer.Exit):
            run(ip="1.2.3.4", requested_server="mybox", yes=True)

    def test_server_flag_resolves_ip_from_registry(self, servers_file: Path, tmp_home: Path) -> None:
        """--server flag with a known name should resolve to its IP."""
        from meridian.servers import ServerEntry, ServerRegistry

        reg = ServerRegistry(servers_file)
        reg.add(ServerEntry("10.20.30.40", "root", "prod"))

        # Verify the registry lookup works (this is what run() does internally)
        entry = reg.find("prod")
        assert entry is not None
        assert entry.host == "10.20.30.40"
        assert entry.user == "root"

    def test_server_name_not_found_exits(self, servers_file: Path, tmp_home: Path) -> None:
        """--server with unknown name and non-IP string should fail."""
        with pytest.raises(typer.Exit):
            run(requested_server="nonexistent", yes=True)

    def test_force_refreshes_credentials_before_deploy(self, tmp_home: Path) -> None:
        """Deploy must refresh from the server before trusting cached local creds."""
        resolved = SimpleNamespace(
            ip="1.2.3.4",
            user="root",
            conn=object(),
            creds_dir=tmp_home / "credentials" / "1.2.3.4",
        )
        resolved.creds_dir.mkdir(parents=True)

        with (
            patch("meridian.commands.setup.resolve_server", return_value=resolved),
            patch("meridian.commands.setup.ensure_server_connection", return_value=resolved),
            patch("meridian.commands.setup._check_ports"),
            patch("meridian.commands.setup.fetch_credentials", return_value=True) as mock_fetch,
            patch("meridian.commands.setup._run_provisioner"),
            patch("meridian.commands.setup._print_success"),
            patch("meridian.commands.setup._offer_relay"),
        ):
            run(ip="1.2.3.4", yes=True)

        mock_fetch.assert_called_once_with(resolved, force=True)

    def test_regenerates_pages_after_deploy(self, tmp_home: Path) -> None:
        resolved = SimpleNamespace(
            ip="1.2.3.4",
            user="root",
            conn=object(),
            creds_dir=tmp_home / "credentials" / "1.2.3.4",
        )
        resolved.creds_dir.mkdir(parents=True)
        creds = ServerCredentials()
        creds.server.ip = "1.2.3.4"
        creds.clients = [ClientEntry(name="default", reality_uuid="r-uuid", wss_uuid="w-uuid")]
        creds.save(resolved.creds_dir / "proxy.yml")

        with (
            patch("meridian.commands.setup.resolve_server", return_value=resolved),
            patch("meridian.commands.setup.ensure_server_connection", return_value=resolved),
            patch("meridian.commands.setup._check_ports"),
            patch("meridian.commands.setup.fetch_credentials", return_value=True),
            patch("meridian.commands.setup._run_provisioner"),
            patch("meridian.commands.setup._regenerate_connection_pages_after_deploy") as mock_regen,
            patch("meridian.commands.setup._print_success"),
            patch("meridian.commands.setup._offer_relay"),
        ):
            run(ip="1.2.3.4", yes=True)

        mock_regen.assert_called_once_with(resolved)


class TestSuccessOutput:
    def _write_proxy(self, creds_dir: Path, *, domain: str = "", geo_block: bool = False) -> None:
        creds = ServerCredentials()
        creds.server.ip = "1.2.3.4"
        creds.server.domain = domain or None
        creds.server.hosted_page = True
        creds.server.geo_block = geo_block
        creds.panel.info_page_path = "connect"
        creds.panel.url = f"https://{domain or '1.2.3.4'}/panel/"
        creds.panel.username = "admin"
        creds.panel.password = "secret"
        creds.reality.uuid = "r-uuid"
        creds.save(creds_dir / "proxy.yml")

    def test_domain_success_includes_cloudflare_steps(self, tmp_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
        creds_dir = tmp_home / "credentials" / "1.2.3.4"
        creds_dir.mkdir(parents=True)
        self._write_proxy(creds_dir, domain="example.com")
        resolved = SimpleNamespace(ip="1.2.3.4", creds_dir=creds_dir)

        _print_success(resolved, "default", "example.com")

        out = capsys.readouterr().err
        assert "Cloudflare setup" in out
        assert "DNS only" in out
        assert "Full (Strict)" in out
        assert "getmeridian.org/ping" not in out

    def test_ip_mode_success_omits_external_ping_hint(self, tmp_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
        creds_dir = tmp_home / "credentials" / "1.2.3.4"
        creds_dir.mkdir(parents=True)
        self._write_proxy(creds_dir)
        resolved = SimpleNamespace(ip="1.2.3.4", creds_dir=creds_dir)

        _print_success(resolved, "default", "")

        out = capsys.readouterr().err
        assert "getmeridian.org/ping" not in out
        assert "Cloudflare setup" not in out

    def test_success_output_mentions_enabled_geo_blocking(
        self, tmp_home: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        creds_dir = tmp_home / "credentials" / "1.2.3.4"
        creds_dir.mkdir(parents=True)
        self._write_proxy(creds_dir, geo_block=True)
        resolved = SimpleNamespace(ip="1.2.3.4", creds_dir=creds_dir)

        _print_success(resolved, "default", "")

        out = capsys.readouterr().err
        assert "Geo-blocking is ON" in out
        assert "--no-geo-block" in out


class TestRegenerateConnectionPagesAfterDeploy:
    def test_calls_regenerator_for_saved_clients(self, tmp_home: Path) -> None:
        creds_dir = tmp_home / "credentials" / "1.2.3.4"
        creds_dir.mkdir(parents=True)
        resolved = SimpleNamespace(ip="1.2.3.4", creds_dir=creds_dir, conn=object())
        creds = ServerCredentials()
        creds.server.ip = "1.2.3.4"
        creds.clients = [ClientEntry(name="alice", reality_uuid="r-uuid", wss_uuid="w-uuid")]
        creds.save(creds_dir / "proxy.yml")

        with patch("meridian.commands.relay._regenerate_client_pages") as mock_regen:
            _regenerate_connection_pages_after_deploy(resolved)

        mock_regen.assert_called_once()


class TestIsIPv4:
    """Test the is_ipv4 helper used by setup."""

    def test_valid_ips(self) -> None:
        assert is_ipv4("1.2.3.4") is True
        assert is_ipv4("255.255.255.255") is True
        assert is_ipv4("0.0.0.0") is True
        assert is_ipv4("192.168.1.1") is True

    def test_invalid_ips(self) -> None:
        assert is_ipv4("") is False
        assert is_ipv4("256.1.1.1") is False
        assert is_ipv4("1.2.3") is False
        assert is_ipv4("1.2.3.4.5") is False
        assert is_ipv4("abc.def.ghi.jkl") is False
        assert is_ipv4("not-an-ip") is False
        assert is_ipv4("1.2.3.-1") is False
