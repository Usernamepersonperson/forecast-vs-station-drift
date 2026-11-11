"""Tiny HTTP layer: urllib only, retries, and a file cache keyed by the caller."""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

USER_AGENT = (
    "forecast-vs-station-drift/0.1 "
    "(+https://github.com/Usernamepersonperson/forecast-vs-station-drift)"
)

# A getter takes (url, headers) and returns the response body.
Getter = Callable[[str, dict[str, str] | None], bytes]


def http_get(
    url: str,
    headers: dict[str, str] | None = None,
    *,
    timeout: float = 120.0,
    retries: int = 4,
    opener=urllib.request.urlopen,
    sleep=time.sleep,
) -> bytes:
    """GET with retry on 429 and 5xx (exponential back-off). Other errors raise immediately."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    for attempt in range(retries):
        try:
            with opener(req, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            retryable = exc.code == 429 or exc.code >= 500
            if not retryable or attempt == retries - 1:
                raise
        except urllib.error.URLError:
            if attempt == retries - 1:
                raise
        sleep(2.0 * 2**attempt)
    raise RuntimeError("unreachable")  # pragma: no cover


def cached_get(
    url: str,
    path: Path,
    getter: Getter = http_get,
    headers: dict[str, str] | None = None,
) -> bytes:
    """Return the cached body at `path` if present, else download it and store it."""
    if path.exists():
        return path.read_bytes()
    body = getter(url, headers)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return body
