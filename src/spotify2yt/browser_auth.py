"""Automatic YouTube Music authentication via browser cookies.

OAuth tokens from custom clients are currently rejected by YouTube Music's
internal API (sigma67/ytmusicapi#813), so the reliable path is browser
authentication. This module reads the ``music.youtube.com`` cookies straight
from the browser's cookie store, so no manual header copy-pasting is needed.
"""

from __future__ import annotations

import json
import logging
from http.cookiejar import CookieJar
from pathlib import Path
from typing import cast

import browser_cookie3

logger = logging.getLogger(__name__)

_AUTH_FILE = Path("browser.json")
_COOKIE_DOMAIN = "music.youtube.com"

# Generic user agents per browser family. YouTube validates that requests
# look like a real browser, so this should stay close to the actual browser.
_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
_USER_AGENTS = {
    "firefox": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0"),
    "chrome": _CHROME_UA,
    "chromium": _CHROME_UA,
    "brave": _CHROME_UA,
    "edge": _CHROME_UA + " Edg/131.0.0.0",
    "opera": _CHROME_UA + " OPR/116.0.0.0",
}

# Cookies that only exist when the user is signed in to YouTube Music.
_LOGIN_COOKIES = ("SAPISID", "__Secure-1PAPISID", "__Secure-3PAPISID")


def _extract_cookies(browser: str | None) -> CookieJar:
    """Load cookies for music.youtube.com from the given (or any) browser."""
    try:
        if browser:
            family = browser.lower()
            loader = getattr(browser_cookie3, family, None)
            if loader is None:
                raise RuntimeError(
                    f"Unsupported browser '{browser}'. Options: {', '.join(sorted(_USER_AGENTS))}."
                )
            return cast("CookieJar", loader(domain_name=_COOKIE_DOMAIN))
        return cast("CookieJar", browser_cookie3.load(domain_name=_COOKIE_DOMAIN))
    except browser_cookie3.BrowserCookieError as exc:
        raise RuntimeError(
            f"Could not read cookies from {browser or 'any browser'}: {exc}. "
            "Make sure the browser is installed, you are signed in to "
            f"{_COOKIE_DOMAIN}, and the browser is closed."
        ) from exc
    except Exception as exc:
        if isinstance(exc, RuntimeError):
            raise
        # The library raises bare TypeError when no profile exists.
        raise RuntimeError(
            f"Could not read cookies from {browser or 'any browser'} "
            f"({type(exc).__name__}). No supported browser profile found."
        ) from exc


def _cookie_header(cookie_jar: CookieJar) -> str:
    """Join the jar into a Cookie header and verify the user is signed in."""
    cookies = list(cookie_jar)
    pairs = [f"{cookie.name}={cookie.value}" for cookie in cookies]
    if not pairs:
        raise RuntimeError(
            f"No cookies found for {_COOKIE_DOMAIN}. "
            "Open https://music.youtube.com and sign in first."
        )

    names = {cookie.name for cookie in cookies}
    if not any(name in names for name in _LOGIN_COOKIES):
        raise RuntimeError(
            f"You are not signed in to {_COOKIE_DOMAIN} in this browser. Sign in and try again."
        )
    return "; ".join(pairs)


def build_browser_headers(browser: str | None = None) -> dict[str, str]:
    """Build YouTube Music auth headers from the browser's cookies."""
    family = (browser or "firefox").lower()
    cookie_jar = _extract_cookies(browser)
    headers = {
        "User-Agent": _USER_AGENTS.get(family, _USER_AGENTS["chrome"]),
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://music.youtube.com",
        "X-Goog-AuthUser": "0",
        "Cookie": _cookie_header(cookie_jar),
    }
    logger.debug("Built browser auth headers (%d cookies).", len(headers["Cookie"]))
    return headers


def auto_authenticate(browser: str | None = None) -> Path:
    """Create a validated auth file from browser cookies.

    Returns the path of the written auth file.
    """
    from ytmusicapi import YTMusic

    headers = build_browser_headers(browser)

    # Validate before writing anything to disk.
    YTMusic(headers).get_library_playlists(limit=1)

    _AUTH_FILE.write_text(json.dumps(headers, indent=2), encoding="utf-8")
    logger.info("Auth file written to %s.", _AUTH_FILE)
    return _AUTH_FILE
