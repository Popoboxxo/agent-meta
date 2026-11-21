"""TDD tests for issue #896 — Admin-UI start modes ``local``/``network``.

Loaded via :mod:`importlib` because ``admin-server.py`` contains a hyphen.
Each test class corresponds to one implementation-plan task (896-1 … 896-5).
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import sys
from pathlib import Path
from unittest import mock

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_ADMIN_SERVER_PATH = _REPO_ROOT / "scripts" / "admin-server.py"
sys.path.insert(0, str(_REPO_ROOT / "scripts"))


def _load_admin_server():
    spec = importlib.util.spec_from_file_location("admin_server_896", _ADMIN_SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["admin_server_896"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


admin_server = _load_admin_server()


# --------------------------------------------------------------------------- #
# Task 896-1: --mode local|network and bind resolution                        #
# --------------------------------------------------------------------------- #


class TestResolveBindMode:
    @pytest.mark.parametrize(
        "mode, cli_host, cfg_bind_host, expected",
        [
            ("local", None, "10.0.0.2", "127.0.0.1"),
            ("network", None, "127.0.0.1", "0.0.0.0"),
            ("network", "10.0.0.2", "127.0.0.1", "10.0.0.2"),
            (None, None, "10.0.0.2", "10.0.0.2"),
        ],
    )
    def test_resolution(self, mode, cli_host, cfg_bind_host, expected):
        assert admin_server._resolve_bind_mode(
            mode=mode, cli_host=cli_host, cfg_bind_host=cfg_bind_host,
        ) == expected

    def test_local_with_non_loopback_cli_host_raises(self):
        with pytest.raises(ValueError):
            admin_server._resolve_bind_mode(
                mode="local", cli_host="0.0.0.0", cfg_bind_host="127.0.0.1",
            )

    def test_mode_flag_registered_exactly_once(self):
        tree = ast_parse_admin_server()
        adds = [
            node for node in ast_walk_calls(tree)
            if is_add_argument(node) and first_string_arg(node) == "--mode"
        ]
        assert len(adds) == 1


def ast_parse_admin_server():
    return ast.parse(_ADMIN_SERVER_PATH.read_text(encoding="utf-8"))


def ast_walk_calls(tree):
    return (n for n in ast.walk(tree) if isinstance(n, ast.Call))


def is_add_argument(node):
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "add_argument"
    )


def first_string_arg(node):
    if node.args and isinstance(node.args[0], ast.Constant):
        return node.args[0].value
    return None


# --------------------------------------------------------------------------- #
# Task 896-2: ephemeral network token (never persisted)                       #
# --------------------------------------------------------------------------- #


class TestNetworkToken:
    def test_existing_token_is_reused_without_generation(self, tmp_path):
        token, generated = admin_server._ensure_network_token("x")
        assert (token, generated) == ("x", False)
        assert list(tmp_path.iterdir()) == []

    def test_none_generates_urlsafe_token_without_persistence(self, tmp_path):
        first, generated = admin_server._ensure_network_token(None)
        assert generated is True
        assert len(first) >= 32
        assert all(c.isalnum() or c in "-_" for c in first)
        assert list(tmp_path.iterdir()) == []

    def test_two_calls_yield_distinct_tokens(self):
        a, _ = admin_server._ensure_network_token(None)
        b, _ = admin_server._ensure_network_token(None)
        assert a != b

    @staticmethod
    def _server(root, **kw):
        with mock.patch.object(admin_server, "_DaemonThreadingHTTPServer"):
            return admin_server.AdminServer(root, port=0, **kw)

    def test_local_path_never_calls_generator(self, tmp_path):
        with mock.patch.object(admin_server, "_ensure_network_token",
                               return_value=("tok", True)) as spy:
            self._server(tmp_path, host="127.0.0.1", mode="local")
        spy.assert_not_called()

    def test_network_path_calls_generator_once(self, tmp_path):
        with mock.patch.object(admin_server, "_ensure_network_token",
                               return_value=("tok", True)) as spy:
            srv = self._server(tmp_path, host="0.0.0.0", mode="network")
        spy.assert_called_once()
        assert srv is not None


# --------------------------------------------------------------------------- #
# Task 896-3: never pass the token via argv or log                            #
# --------------------------------------------------------------------------- #


class TestDetachedTokenTransport:
    TOKEN = "example-network-token-896"

    @staticmethod
    def _args(root, **kw):
        ns = dict(root=str(root), host="0.0.0.0", port=7421, admin_token=None,
                  allowed_hosts=None, watch=False, no_viz=True, mode="network")
        ns.update(kw)
        return argparse.Namespace(**ns)

    def test_token_via_env_not_argv_and_absent_from_log(self, tmp_path):
        captured = {}

        def fake_popen(cmd, **kw):
            captured["cmd"] = cmd
            captured["env"] = kw.get("env")
            kw["stdout"].write("  i  child started\n")
            kw["stdout"].flush()
            return mock.Mock(pid=4242, poll=lambda: None, terminate=mock.Mock())

        with mock.patch.object(admin_server.subprocess, "Popen", fake_popen), \
             mock.patch.object(admin_server, "_tmp_sink_env", lambda r, base=None: {"PATH": "/x"}), \
             mock.patch.object(admin_server, "_probe_port_bindable", lambda h, p: (True, "")), \
             mock.patch.object(admin_server, "_pid_starttime", lambda p: None), \
             mock.patch.object(admin_server, "_wait_for_admin", lambda *a, **k: (True, "")):
            admin_server._admin_start_detached(
                self._args(tmp_path), network_token=self.TOKEN,
            )

        assert "--admin-token" not in captured["cmd"]
        assert self.TOKEN not in captured["cmd"]
        assert captured["env"]["ADMIN_UI_TOKEN"] == self.TOKEN
        log_text = (tmp_path / admin_server.ADMIN_LOG_FILE).read_text(encoding="utf-8")
        assert self.TOKEN not in log_text


# --------------------------------------------------------------------------- #
# Task 896-4: reachable URLs, firewall hint, security warning                 #
# --------------------------------------------------------------------------- #


class TestNetworkBanner:
    TOKEN = "EXAMPLE_TOKEN_896_XYZ"

    def test_reachable_urls_wildcard_excludes_wildcard_address(self):
        urls = admin_server._reachable_urls("0.0.0.0", 7420, ("192.168.1.5",))
        assert "http://192.168.1.5:7420/" in urls
        assert "http://127.0.0.1:7420/" in urls
        assert not any("0.0.0.0" in url for url in urls)

    def test_reachable_urls_concrete_address(self):
        assert admin_server._reachable_urls(
            "10.0.0.2", 7420, ("192.168.1.5",),
        ) == ["http://10.0.0.2:7420/"]

    def test_banner_has_token_urls_firewall_and_security_warning(self):
        urls = admin_server._reachable_urls("0.0.0.0", 7420, ("192.168.1.5",))
        joined = "\n".join(admin_server._network_banner(urls, self.TOKEN, 7420))
        assert f"http://192.168.1.5:7420/?token={self.TOKEN}" in joined
        assert f"Token: {self.TOKEN}" in joined
        assert "Allow inbound TCP 7420" in joined
        assert "firewall" in joined.lower() or "security group" in joined.lower()
        assert "password" in joined.lower()
        assert "TLS" in joined
        assert "ssh" in joined.lower()

    def test_server_start_never_prints_token(self, tmp_path, capsys):
        srv = admin_server.AdminServer(
            tmp_path, host="0.0.0.0", port=7420,
            admin_token=self.TOKEN, enable_watcher=False, enable_viz=False,
        )
        srv.httpd = mock.Mock()
        srv.start()
        out = capsys.readouterr().out
        assert self.TOKEN not in out
        assert "http://192.168.1.5:7420/" not in out  # no fabricated IPs here
        assert "http://127.0.0.1:7420/" in out


# --------------------------------------------------------------------------- #
# Task 896-5: skill/command docs, port matrix, decision 31                    #
# --------------------------------------------------------------------------- #


class TestAdminModeDocs:
    @staticmethod
    def _read(rel: str) -> str:
        return (_REPO_ROOT / rel).read_text(encoding="utf-8")

    def test_admin_docs_cover_start_modes(self):
        command = self._read("commands/1-generic/admin.md")
        rule = self._read("rules/2-platform/agent-meta-admin-ui.md")
        howto = self._read("docs/howto/admin-ui-remote-access.md")
        reference = self._read("docs/api/admin-ui-reference.md")

        assert "--mode" in command

        for token in ("7420", "8765", "9090", "Firewall",
                      "Sicherheitswarnung", "Entscheidung 31"):
            assert token in rule, f"rule missing {token!r}"

        for token in ("--mode", "7420", "8765", "9090", "firewall",
                      "Entscheidung 31", "not persisted"):
            assert token.lower() in howto.lower(), f"howto missing {token!r}"

        for token in ("7420", "8765", "9090", "--mode", "Entscheidung 31"):
            assert token in reference, f"reference missing {token!r}"
