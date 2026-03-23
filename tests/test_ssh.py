"""Tests for SSH connection helpers and tcp_connect."""

from __future__ import annotations

import subprocess
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import typer

from meridian.ssh import ServerConnection, tcp_connect


class TestServerConnectionInit:
    def test_defaults(self) -> None:
        conn = ServerConnection(ip="1.2.3.4")
        assert conn.ip == "1.2.3.4"
        assert conn.user == "root"
        assert conn.local_mode is False
        assert conn.needs_sudo is False

    def test_custom_user(self) -> None:
        conn = ServerConnection(ip="1.2.3.4", user="ubuntu")
        assert conn.user == "ubuntu"

    def test_local_mode(self) -> None:
        conn = ServerConnection(ip="1.2.3.4", local_mode=True)
        assert conn.local_mode is True


class TestServerConnectionRun:
    def test_remote_command_uses_ssh(self) -> None:
        conn = ServerConnection(ip="1.2.3.4", user="root")
        with patch("meridian.ssh.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok\n", stderr="")
            conn.run("echo hello")
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            assert "ssh" in cmd
            assert "root@1.2.3.4" in cmd
            assert "echo hello" in cmd

    def test_local_mode_uses_bash(self) -> None:
        conn = ServerConnection(ip="1.2.3.4", local_mode=True)
        with patch("meridian.ssh.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok\n", stderr="")
            conn.run("echo hello")
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            assert cmd == ["bash", "-c", "echo hello"]

    def test_local_mode_needs_sudo(self) -> None:
        conn = ServerConnection(ip="1.2.3.4", local_mode=True)
        conn.needs_sudo = True
        with patch("meridian.ssh.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok\n", stderr="")
            conn.run("cat /etc/meridian/proxy.yml")
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            assert cmd == ["sudo", "-n", "bash", "-c", "cat /etc/meridian/proxy.yml"]

    def test_remote_includes_ssh_opts(self) -> None:
        conn = ServerConnection(ip="5.6.7.8", user="deploy")
        with patch("meridian.ssh.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
            conn.run("whoami")
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            assert "BatchMode=yes" in cmd
            assert "ConnectTimeout=5" in cmd
            assert "StrictHostKeyChecking=yes" in cmd

    def test_stdin_devnull(self) -> None:
        conn = ServerConnection(ip="1.2.3.4")
        with patch("meridian.ssh.subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
            conn.run("echo test")
            kwargs = mock_run.call_args[1]
            assert kwargs["stdin"] == subprocess.DEVNULL


class TestTcpConnect:
    def test_returns_true_on_success(self) -> None:
        mock_sock = MagicMock()
        with patch("socket.socket", return_value=mock_sock):
            assert tcp_connect("1.2.3.4", 443) is True
            mock_sock.settimeout.assert_called_once_with(5)
            mock_sock.connect.assert_called_once_with(("1.2.3.4", 443))
            mock_sock.close.assert_called_once()

    def test_returns_false_on_connection_refused(self) -> None:
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = ConnectionRefusedError
        with patch("socket.socket", return_value=mock_sock):
            assert tcp_connect("1.2.3.4", 443) is False

    def test_returns_false_on_timeout(self) -> None:
        import socket

        mock_sock = MagicMock()
        mock_sock.connect.side_effect = socket.timeout
        with patch("socket.socket", return_value=mock_sock):
            assert tcp_connect("1.2.3.4", 443) is False

    def test_returns_false_on_os_error(self) -> None:
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = OSError("Network unreachable")
        with patch("socket.socket", return_value=mock_sock):
            assert tcp_connect("1.2.3.4", 443) is False

    def test_custom_timeout(self) -> None:
        mock_sock = MagicMock()
        with patch("socket.socket", return_value=mock_sock):
            tcp_connect("1.2.3.4", 80, timeout=10)
            mock_sock.settimeout.assert_called_once_with(10)


class TestCheckSSH:
    def test_local_mode_skips_check(self) -> None:
        conn = ServerConnection(ip="1.2.3.4", local_mode=True)
        # Should return without doing anything
        conn.check_ssh()  # no exception

    @patch("meridian.ssh._host_key_known", return_value=True)
    def test_ssh_success(self, _mock_hk: Any) -> None:
        conn = ServerConnection(ip="1.2.3.4")
        with patch.object(conn, "run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok\n", stderr="")
            conn.check_ssh()  # should not raise

    @patch("meridian.ssh._host_key_known", return_value=True)
    def test_ssh_failure_exits(self, _mock_hk: Any) -> None:
        conn = ServerConnection(ip="1.2.3.4")
        with patch.object(conn, "run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=255, stdout="", stderr="Permission denied"
            )
            with pytest.raises(typer.Exit):
                conn.check_ssh()

    @patch("meridian.ssh._host_key_known", return_value=True)
    def test_ssh_timeout_exits(self, _mock_hk: Any) -> None:
        conn = ServerConnection(ip="1.2.3.4")
        with patch.object(conn, "run", side_effect=subprocess.TimeoutExpired(cmd="ssh", timeout=10)):
            with pytest.raises(typer.Exit):
                conn.check_ssh()

    @patch("meridian.ssh._host_key_known", return_value=True)
    def test_ssh_not_found_exits(self, _mock_hk: Any) -> None:
        conn = ServerConnection(ip="1.2.3.4")
        with patch.object(conn, "run", side_effect=FileNotFoundError):
            with pytest.raises(typer.Exit):
                conn.check_ssh()

    @patch("meridian.ssh._verify_host_key", return_value=False)
    @patch("meridian.ssh._host_key_known", return_value=False)
    def test_unknown_host_key_rejected_exits(self, _mock_hk: Any, _mock_vhk: Any) -> None:
        conn = ServerConnection(ip="1.2.3.4")
        with pytest.raises(typer.Exit):
            conn.check_ssh()

    @patch("meridian.ssh._verify_host_key", return_value=True)
    @patch("meridian.ssh._host_key_known", return_value=False)
    def test_unknown_host_key_accepted_continues(self, _mock_hk: Any, _mock_vhk: Any) -> None:
        conn = ServerConnection(ip="1.2.3.4")
        with patch.object(conn, "run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok\n", stderr="")
            conn.check_ssh()  # should not raise
