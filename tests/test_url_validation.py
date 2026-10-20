"""Unit tests for utils/url_validation.py"""

import pytest

from utils.url_validation import MAX_URL_LENGTH, InvalidURLError, normalize_url


def test_accepts_https_url_unchanged():
    assert normalize_url("https://example.com") == "https://example.com"


def test_accepts_http_url_unchanged():
    assert normalize_url("http://example.com") == "http://example.com"


def test_lowercases_scheme_and_host_only():
    assert normalize_url("HTTPS://Example.COM/Path") == "https://example.com/Path"


def test_bare_domain_gets_https_prefix():
    assert normalize_url("example.com") == "https://example.com"


def test_bare_domain_with_path_and_query():
    assert (
        normalize_url("example.com/docs?a=1")
        == "https://example.com/docs?a=1"
    )


def test_bare_domain_with_port_is_not_mistaken_for_a_scheme():
    assert normalize_url("example.com:8080/x") == "https://example.com:8080/x"


def test_strips_surrounding_whitespace():
    assert normalize_url("  https://example.com  ") == "https://example.com"


def test_removes_default_https_port():
    assert normalize_url("https://example.com:443/x") == "https://example.com/x"


def test_removes_default_http_port():
    assert normalize_url("http://example.com:80/") == "http://example.com/"


def test_keeps_query_and_fragment():
    assert (
        normalize_url("https://example.com/p?q=1#frag")
        == "https://example.com/p?q=1#frag"
    )


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "JavaScript:alert(document.cookie)",
        "data:text/html,<script>alert(1)</script>",
        "file:///etc/passwd",
        "vbscript:msgbox(1)",
        "ftp://example.com/file",
        "mailto:someone@example.com",
    ],
)
def test_rejects_disallowed_schemes(url):
    with pytest.raises(InvalidURLError):
        normalize_url(url)


def test_rejects_empty_and_whitespace_only():
    with pytest.raises(InvalidURLError):
        normalize_url("")
    with pytest.raises(InvalidURLError):
        normalize_url("   ")


def test_rejects_non_string():
    with pytest.raises(InvalidURLError):
        normalize_url(None)  # type: ignore[arg-type]


def test_rejects_control_characters_and_embedded_whitespace():
    with pytest.raises(InvalidURLError):
        normalize_url("https://exam\tple.com")
    with pytest.raises(InvalidURLError):
        normalize_url("https://example.com/\npath")
    with pytest.raises(InvalidURLError):
        normalize_url("not a url")


def test_rejects_url_over_max_length():
    with pytest.raises(InvalidURLError):
        normalize_url("https://e.com/" + "a" * MAX_URL_LENGTH)


def test_accepts_url_at_exact_max_length():
    url = "https://example.com/" + "a" * (MAX_URL_LENGTH - len("https://example.com/"))
    assert len(url) == MAX_URL_LENGTH
    assert normalize_url(url) == url


def test_rejects_missing_host():
    with pytest.raises(InvalidURLError):
        normalize_url("https://")
    with pytest.raises(InvalidURLError):
        normalize_url("http:///path")


def test_rejects_malformed_port():
    with pytest.raises(InvalidURLError):
        normalize_url("https://example.com:notaport")


def test_rejects_unmatched_bracket():
    with pytest.raises(InvalidURLError):
        normalize_url("https://[::1")
