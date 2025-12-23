from __future__ import annotations

import importlib.metadata


try:
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:  # pragma: no cover
    # Allows importing gmuse directly from the source tree (e.g., during Sphinx
    # builds) without requiring the package to be installed.
    __version__ = "0.0.0"
