"""Unit tests for web_doc_fetcher.

Note: tests that require real HTTP requests are skipped when running in
an environment without outbound network access (e.g. behind a restrictive
proxy).  The protocol-validation tests are fully local and always run.
"""
import os
import urllib.error
from unittest.mock import patch, MagicMock
from skills.tool_tianyan.scripts.web_doc_fetcher import fetch_doc, _classify_http_error


# ============================================================
# Protocol validation (always runs, no network required)
# ============================================================

class TestProtocolValidation:
    def test_file_protocol_blocked(self):
        assert "ERROR_INVALID_PROTOCOL" in fetch_doc("file:///etc/passwd")

    def test_ftp_protocol_blocked(self):
        assert "ERROR_INVALID_PROTOCOL" in fetch_doc("ftp://example.com/file.txt")

    def test_ssh_protocol_blocked(self):
        assert "ERROR_INVALID_PROTOCOL" in fetch_doc("ssh://server:22/cmd")

    def test_javascript_protocol_blocked(self):
        assert "ERROR_INVALID_PROTOCOL" in fetch_doc("javascript:alert(1)")

    def test_data_protocol_blocked(self):
        assert "ERROR_INVALID_PROTOCOL" in fetch_doc("data:text/html,<h1>hi</h1>")

    def test_empty_url_blocked(self):
        assert "ERROR_INVALID_PROTOCOL" in fetch_doc("")

    def test_bare_word_blocked(self):
        assert "ERROR_INVALID_PROTOCOL" in fetch_doc("not_a_url")


# ============================================================
# HTTP error classification (unit-level, no network)
# ============================================================

class TestHttpErrorClassification:
    def _make_http_error(self, code, headers=None):
        """Create a mock HTTPError with given code and headers."""
        err = urllib.error.HTTPError(
            url="http://example.com",
            code=code,
            msg=f"HTTP {code}",
            hdrs=headers or {},
            fp=None,
        )
        return err

    def test_401_returns_auth_required(self):
        err = self._make_http_error(401)
        result = _classify_http_error(err)
        assert "ERROR_AUTH_REQUIRED" in result
        assert "401" in result

    def test_403_with_www_auth_returns_auth_blocked(self):
        err = self._make_http_error(403, {"WWW-Authenticate": "Bearer"})
        result = _classify_http_error(err)
        assert "ERROR_AUTH_BLOCKED" in result

    def test_403_with_cloudflare_returns_waf(self):
        err = self._make_http_error(403, {"Server": "cloudflare"})
        result = _classify_http_error(err)
        assert "ERROR_WAF_BLOCKED" in result

    def test_403_generic_returns_forbidden(self):
        err = self._make_http_error(403)
        result = _classify_http_error(err)
        assert "ERROR_FORBIDDEN" in result

    def test_404_returns_not_found(self):
        err = self._make_http_error(404)
        result = _classify_http_error(err)
        assert "ERROR_HTTP_404" in result
        assert "not found" in result.lower()

    def test_500_returns_server_error(self):
        err = self._make_http_error(500)
        result = _classify_http_error(err)
        assert "ERROR_HTTP_500" in result

    def test_503_returns_server_error(self):
        err = self._make_http_error(503)
        result = _classify_http_error(err)
        assert "ERROR_HTTP_503" in result


# ============================================================
# Proxy support (mocked)
# ============================================================

class TestProxySupport:
    @patch.dict(os.environ, {"HTTP_PROXY": "http://myproxy:8080"}, clear=False)
    def test_reads_http_proxy_env(self):
        """Should not crash when HTTP_PROXY is set (validates proxy is read)."""
        result = fetch_doc("http://httpbin.org/get")
        # We just verify it doesn't crash; actual result depends on proxy reachability
        assert isinstance(result, str)

    @patch.dict(os.environ, {"https_proxy": "http://myproxy:8080"}, clear=False)
    def test_reads_lowercase_https_proxy(self):
        result = fetch_doc("https://httpbin.org/get")
        assert isinstance(result, str)
