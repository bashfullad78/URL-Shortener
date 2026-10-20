"""URL validation and normalization for shortened links.
- Domains like ``example.com`` are normalized by prepending ``https://``. 
- Reject everything else aka ``javascript:``, ``data:``, ``file:`` and any other
  scheme, and/or badly formed input. 
"""

import re  
from urllib.parse import urlsplit, urlunsplit

MAX_URL_LENGTH = 2048
ALLOWED_SCHEMES = ("http", "https")

# scheme: prefix without "//" — checked first so callers get a clear error
_SCHEME_PREFIX_RE = re.compile(r"^([A-Za-z][A-Za-z0-9+.\-]*):")
# A colon that is actual host:port (e.g. example.com:8080/path).
_PORT_LOOKS_LIKE_RE = re.compile(r"^\d{1,5}(?:[/?#]|$)")


class InvalidURLError(ValueError):
    """Raised when a candidate URL cannot be accepted."""


def normalize_url(raw: str) -> str:
    """Validate and normalize a URL for storage.

    Returns the canonical form (lowercased scheme/host, default ports
    stripped). Raises :class:`InvalidURLError` with a readable message
    for anything that are not to be shortened.
    """
    if not isinstance(raw, str) or not raw.strip():
        raise InvalidURLError("URL must be a non-empty string")

    url = raw.strip()
    if len(url) > MAX_URL_LENGTH:
        raise InvalidURLError(f"URL exceeds {MAX_URL_LENGTH} characters")
    # Raw control characters/embedded whitespace, spaces included are
    # never valid unencoded in a URL.
    if any(ord(c) <= 0x20 or ord(c) == 0x7F for c in url):
        raise InvalidURLError("URL contains control characters or whitespace")

    scheme_match = _SCHEME_PREFIX_RE.match(url)
    if scheme_match:
        scheme = scheme_match.group(1).lower()
        rest = url[scheme_match.end():]
        if scheme in ALLOWED_SCHEMES and rest.startswith("//"):
            pass  # normal http(s):// URL
        elif _PORT_LOOKS_LIKE_RE.match(rest):
            url = "https://" + url  # bare domain with port
        else:
            raise InvalidURLError(
                f"URL scheme '{scheme}:' is not allowed — use http:// or https://"
            )
    else:
        url = "https://" + url  # bare domain

    try:
        parts = urlsplit(url)
        port = parts.port  # raises ValueError on a badformed port
    except ValueError as exc:
        raise InvalidURLError(f"Malformed URL: {exc}") from exc

    scheme = parts.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise InvalidURLError(
            f"URL scheme '{scheme}:' is not allowed — use http:// or https://"
        )

    host = parts.hostname
    if not host:
        raise InvalidURLError("URL must include a host")

    # Canonical netloc: lowercase host, keep userinfo and port unless the port
    # is scheme's default 
    netloc = host.lower()
    if port is not None and port != (80 if scheme == "http" else 443):
        netloc = f"{netloc}:{port}"

    return urlunsplit((scheme, netloc, parts.path, parts.query, parts.fragment))
