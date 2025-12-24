from __future__ import annotations

import os
from typing import Iterator

import pytest


@pytest.fixture(autouse=True)
def _isolate_gmuse_global_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> Iterator[None]:
    """Isolate tests from user machine configuration and environment.

    The CLI loads global config from the XDG location (e.g., ~/.config/gmuse/config.toml)
    and also supports GMUSE_* environment variables. If a developer has these set,
    integration/unit tests can become non-deterministic.

    This fixture:
    - redirects XDG_CONFIG_HOME to a per-test temp directory
    - clears any GMUSE_* env vars (tests can still set them explicitly)
    - clears common provider API key env vars to avoid accidental provider detection
    """
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    for key in list(os.environ.keys()):
        if key.startswith("GMUSE_"):
            monkeypatch.delenv(key, raising=False)

    for key in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    yield
