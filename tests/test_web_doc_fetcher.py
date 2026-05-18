import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from skills.tool_tianyan.scripts.web_doc_fetcher import fetch_doc


def test_fetch_doc_invalid_protocol_file():
    """file:// protocol should be blocked."""
    result = fetch_doc("file:///etc/passwd")
    assert "ERROR_INVALID_PROTOCOL" in result


def test_fetch_doc_invalid_protocol_ftp():
    """ftp:// protocol should be blocked."""
    result = fetch_doc("ftp://example.com/file.txt")
    assert "ERROR_INVALID_PROTOCOL" in result


def test_fetch_doc_valid_http():
    """http:// protocol should be accepted (may fail network-wise but not protocol-wise)."""
    result = fetch_doc("http://example.com")
    assert "ERROR_INVALID_PROTOCOL" not in result
