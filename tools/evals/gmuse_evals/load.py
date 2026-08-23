"""Deterministic TOML discovery and construction for eval assets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar

try:  # pragma: no cover - exercised on Python 3.10
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

from pydantic import BaseModel, ValidationError

from .models import EvalCase, EvalFixture, EvalRubric, EvalSuite

ModelT = TypeVar("ModelT", bound=BaseModel)


class EvalLoadError(ValueError):
    """Raised when checked-in eval assets cannot be loaded safely."""


@dataclass(frozen=True)
class EvalAssets:
    """All discovered eval records indexed by their stable IDs."""

    fixtures: dict[str, EvalFixture]
    rubrics: dict[str, EvalRubric]
    cases: dict[str, EvalCase]
    suites: dict[str, EvalSuite]


_ASSET_MODELS: dict[str, type[BaseModel]] = {
    "fixtures": EvalFixture,
    "rubrics": EvalRubric,
    "cases": EvalCase,
    "suites": EvalSuite,
}


def discover_asset_files(evals_dir: Path | str, kind: str) -> list[Path]:
    """Return sorted TOML paths for one asset kind.

    Args:
        evals_dir: Root containing ``fixtures``, ``rubrics``, ``cases`` and
            ``suites`` directories.
        kind: One of the four asset directory names.

    Raises:
        EvalLoadError: If the directory is missing or unsupported.
    """
    if kind not in _ASSET_MODELS:
        raise EvalLoadError(f"unsupported eval asset kind: {kind}")
    directory = Path(evals_dir) / kind
    if not directory.is_dir():
        raise EvalLoadError(f"missing eval asset directory: {directory}")
    return sorted(path for path in directory.glob("*.toml") if path.is_file())


def _documents(data: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    """Accept a single-record document and a useful collection wrapper."""
    wrapped = data.get(kind)
    if wrapped is not None:
        if not isinstance(wrapped, list) or not all(
            isinstance(item, dict) for item in wrapped
        ):
            raise ValueError(f"top-level {kind} must be an array of tables")
        return wrapped
    return [data]


def _load_kind(evals_dir: Path | str, kind: str) -> dict[str, Any]:
    model_type = _ASSET_MODELS[kind]
    records: dict[str, Any] = {}
    for path in discover_asset_files(evals_dir, kind):
        try:
            with path.open("rb") as stream:
                data = tomllib.load(stream)
            if not isinstance(data, dict):
                raise ValueError("document root must be a TOML table")
            documents = _documents(data, kind)
        except (OSError, tomllib.TOMLDecodeError, ValueError) as error:
            raise EvalLoadError(f"failed to parse {path}: {error}") from error

        for index, document in enumerate(documents):
            try:
                model = model_type.model_validate(document)
            except ValidationError as error:
                suffix = f" document {index + 1}" if len(documents) > 1 else ""
                raise EvalLoadError(
                    f"invalid {kind[:-1]} in {path}{suffix}: {error}"
                ) from error
            record_id = getattr(model, "id", None)
            if not isinstance(record_id, str):
                raise EvalLoadError(f"missing stable id in {path}")
            if record_id in records:
                raise EvalLoadError(f"duplicate {kind[:-1]} id '{record_id}'")
            records[record_id] = model
    return records


def load_assets(evals_dir: Path | str = "evals") -> EvalAssets:
    """Load every eval asset kind in deterministic order."""
    root = Path(evals_dir)
    return EvalAssets(
        fixtures=_load_kind(root, "fixtures"),
        rubrics=_load_kind(root, "rubrics"),
        cases=_load_kind(root, "cases"),
        suites=_load_kind(root, "suites"),
    )


def load_suite_assets(
    evals_dir: Path | str = "evals", suite_id: str = "smoke"
) -> tuple[EvalAssets, EvalSuite]:
    """Load all assets and return a named suite or an actionable error."""
    assets = load_assets(evals_dir)
    try:
        return assets, assets.suites[suite_id]
    except KeyError as error:
        available = ", ".join(sorted(assets.suites)) or "none"
        raise EvalLoadError(
            f"unknown suite '{suite_id}'; available suites: {available}"
        ) from error
