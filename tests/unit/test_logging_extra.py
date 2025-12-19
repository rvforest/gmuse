"""Additional unit tests for gmuse.logging.

Targets uncovered branches:
- File handler creation and formatter in `setup_logger`
- `get_logger` using `GMUSE_LOG_FILE` env var
- `configure_litellm_logging` handling when `litellm` module exposes `suppress_debug_info`
- Ensure `setup_logger` respects existing handlers (already covered but keep focused tests small)
"""

from __future__ import annotations

import logging
import sys
import types
from pathlib import Path

import pytest

from gmuse import logging as gmuse_logging


def test_setup_logger_creates_file_and_formatter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GMUSE_DEBUG", raising=False)
    log_file = tmp_path / "subdir" / "gmuse.log"

    logger = gmuse_logging.setup_logger(name="gmuse.tests.file", log_file=str(log_file))

    # FileHandler should be installed and file should be created
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    assert log_file.exists()

    # Formatter for file handlers should include asctime and level
    fh = next(h for h in logger.handlers if isinstance(h, logging.FileHandler))
    assert fh.formatter is not None
    assert fh.formatter._fmt == "[%(asctime)s] [%(levelname)s] %(message)s"
    assert Path(fh.baseFilename) == log_file


def test_get_logger_respects_gmuse_log_file_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("GMUSE_DEBUG", raising=False)
    log_file = tmp_path / "env.log"
    monkeypatch.setenv("GMUSE_LOG_FILE", str(log_file))

    # Ensure we get a logger that writes to the file from env var
    logger = gmuse_logging.get_logger(name="gmuse.tests.env")
    assert any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    assert log_file.exists()


def test_configure_litellm_logging_sets_suppress_when_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Ensure non-debug behavior sets litellm.suppress_debug_info when attribute exists
    monkeypatch.delenv("GMUSE_DEBUG", raising=False)

    litellm = types.ModuleType("litellm")
    setattr(litellm, "suppress_debug_info", False)
    monkeypatch.setitem(sys.modules, "litellm", litellm)

    gmuse_logging.configure_litellm_logging()

    assert getattr(litellm, "suppress_debug_info") is True
    assert logging.getLogger("litellm").level == logging.WARNING


def test_configure_litellm_logging_debug_does_not_modify_suppress(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # If debug is enabled we set log level to DEBUG and do not modify the module attribute
    monkeypatch.setenv("GMUSE_DEBUG", "1")

    litellm = types.ModuleType("litellm")
    setattr(litellm, "suppress_debug_info", False)
    monkeypatch.setitem(sys.modules, "litellm", litellm)

    gmuse_logging.configure_litellm_logging()

    assert getattr(litellm, "suppress_debug_info") is False
    assert logging.getLogger("litellm").level == logging.DEBUG
