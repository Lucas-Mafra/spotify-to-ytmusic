"""Tests for the browser cookie authentication helpers."""

import json
import sys
from types import ModuleType
from typing import Any

import pytest

from spotify2yt import browser_auth


class FakeCookie:
    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value


class TestCookieHeader:
    def test_joins_pairs(self) -> None:
        jar = [FakeCookie("SAPISID", "token"), FakeCookie("PREF", "x")]
        assert browser_auth._cookie_header(jar) == "SAPISID=token; PREF=x"  # type: ignore[arg-type]

    def test_empty_jar_raises(self) -> None:
        with pytest.raises(RuntimeError, match="No cookies found"):
            browser_auth._cookie_header([])  # type: ignore[arg-type]

    def test_not_signed_in_raises(self) -> None:
        jar = [FakeCookie("PREF", "x"), FakeCookie("VISITOR_INFO", "y")]
        with pytest.raises(RuntimeError, match="not signed in"):
            browser_auth._cookie_header(jar)  # type: ignore[arg-type]

    def test_login_cookie_is_enough(self) -> None:
        jar = [FakeCookie("SAPISID", "token")]
        header = browser_auth._cookie_header(jar)  # type: ignore[arg-type]
        assert header == "SAPISID=token"


class TestBuildBrowserHeaders:
    def test_contains_cookie_and_user_agent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            browser_auth,
            "_extract_cookies",
            lambda browser: [FakeCookie("SAPISID", "token")],  # type: ignore[arg-type,return-value]
        )

        headers = browser_auth.build_browser_headers("firefox")

        assert headers["Cookie"] == "SAPISID=token"
        assert "Firefox" in headers["User-Agent"]
        assert headers["Origin"] == "https://music.youtube.com"

    def test_unknown_browser_falls_back_to_chrome_ua(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            browser_auth,
            "_extract_cookies",
            lambda browser: [FakeCookie("__Secure-3PAPISID", "t")],  # type: ignore[arg-type,return-value]
        )

        headers = browser_auth.build_browser_headers("netscape")

        assert headers["User-Agent"] == browser_auth._USER_AGENTS["chrome"]


class TestExtractCookies:
    def test_unsupported_browser_raises(self) -> None:
        with pytest.raises(RuntimeError, match="Unsupported browser"):
            browser_auth._extract_cookies("netscape")


class TestAutoAuthenticate:
    def test_writes_validated_auth_file(
        self, tmp_path: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(
            browser_auth,
            "build_browser_headers",
            lambda browser=None: {"Cookie": "SAPISID=t"},
        )

        class FakeYTMusic:
            def __init__(self, headers: dict[str, str]):
                self.headers = headers

            def get_library_playlists(self, limit: int = 100) -> list[Any]:
                return []

        fake_module = ModuleType("ytmusicapi")
        fake_module.YTMusic = FakeYTMusic  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "ytmusicapi", fake_module)

        path = browser_auth.auto_authenticate("chrome")

        assert path.name == "browser.json"
        assert json.loads((tmp_path / "browser.json").read_text()) == {"Cookie": "SAPISID=t"}
