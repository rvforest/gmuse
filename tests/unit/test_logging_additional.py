"""Unit tests for gmuse.logging.

Focus on debug env behavior and safe litellm logging configuration.
"""

from __future__ import annotations

import builtins
import logging

import pytest

from gmuse import logging as gmuse_logging


def test_setup_logger_respects_debug_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GMUSE_DEBUG", "1")

    logger = gmuse_logging.setup_logger(name="gmuse.tests.debug")
    assert logger.level == logging.DEBUG


def test_setup_logger_does_not_duplicate_handlers() -> None:
    name = "gmuse.tests.handlers"

    logger1 = gmuse_logging.setup_logger(name=name)
    count1 = len(logger1.handlers)

    logger2 = gmuse_logging.setup_logger(name=name)
    count2 = len(logger2.handlers)

    assert logger1 is logger2
    assert count1 == 1
    assert count2 == 1


def test_configure_litellm_logging_importerror_is_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GMUSE_DEBUG", raising=False)

    original_import = builtins.__import__

    def fake_import(name: str, *args, **kwargs):
        if name == "litellm":
            raise ImportError("no litellm")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    gmuse_logging.configure_litellm_logging()

    assert logging.getLogger("litellm").level == logging.WARNING


def test_configure_litellm_logging_debug_sets_debug_level(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GMUSE_DEBUG", "true")

    gmuse_logging.configure_litellm_logging()

    assert logging.getLogger("litellm").level == logging.DEBUG
