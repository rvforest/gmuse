"""Deterministic TOML discovery and construction for eval assets."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # pragma: no cover - exercised on Python 3.10
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

from pydantic import BaseModel, ValidationError

from .models import EvalCase, EvalFixture, EvalRubric, EvalSuite, ValidationIssue


class EvalLoadError(ValueError):
    """Signal that checked-in eval assets cannot be loaded safely.

    A dedicated exception lets the CLI distinguish catalog failures from
    domain-validation reports.

    Example:
        >>> raise EvalLoadError("missing eval asset directory")
        Traceback (most recent call last):
        ...
        EvalLoadError: missing eval asset directory
    """


@dataclass(frozen=True)
class EvalAssets:
    """Eval records and selected-graph load issues indexed by stable IDs.

    Keeping partial records with structured issues allows one validation run to
    report every broken transitive reference.

    Attributes:
        fixtures: Fixture records keyed by fixture ID.
        rubrics: Rubric records keyed by rubric ID.
        cases: Case records keyed by case ID.
        suites: Suite records keyed by suite ID.
        issues: Structural or reference issues found during graph loading.

    Example:
        >>> assets = EvalAssets({}, {}, {}, {})
        >>> assets.issues
        ()
    """

    fixtures: dict[str, EvalFixture]
    rubrics: dict[str, EvalRubric]
    cases: dict[str, EvalCase]
    suites: dict[str, EvalSuite]
    issues: tuple[ValidationIssue, ...] = ()


@dataclass(frozen=True)
class _RawDocument:
    """A parseable document retained until the requested graph is known."""

    path: Path
    index: int
    data: dict[str, Any]


@dataclass(frozen=True)
class _RawCatalog:
    """All parseable, ID-bearing documents indexed without model validation."""

    records: dict[str, dict[str, _RawDocument]]


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

    Returns:
        Sorted TOML paths directly inside the requested asset directory.

    Example:
        >>> discover_asset_files("evals", "suites")
        [PosixPath('evals/suites/core.toml'), PosixPath('evals/suites/smoke.toml')]
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


def _discover_raw_catalog(evals_dir: Path | str) -> _RawCatalog:
    """Parse every asset file and index IDs before validating any model."""
    records: dict[str, dict[str, _RawDocument]] = {}
    for kind in _ASSET_MODELS:
        kind_records: dict[str, _RawDocument] = {}
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
                record_id = document.get("id")
                if not isinstance(record_id, str):
                    continue
                if record_id in kind_records:
                    raise EvalLoadError(f"duplicate {kind[:-1]} id '{record_id}'")
                kind_records[record_id] = _RawDocument(path, index, document)
        records[kind] = kind_records
    return _RawCatalog(records)


def _build_raw_model(catalog: _RawCatalog, kind: str, record_id: str) -> Any:
    """Validate one requested raw document and preserve its source context."""
    document = catalog.records[kind].get(record_id)
    if document is None:
        raise EvalLoadError(f"missing {kind[:-1]} '{record_id}'")
    model_type = _ASSET_MODELS[kind]
    try:
        return model_type.model_validate(document.data)
    except ValidationError as error:
        suffix = f" document {document.index + 1}" if document.index else ""
        raise EvalLoadError(
            f"invalid {kind[:-1]} in {document.path}{suffix}: {error}"
        ) from error


def _try_build_raw_model(
    catalog: _RawCatalog,
    kind: str,
    record_id: str,
    issues: list[ValidationIssue],
) -> Any | None:
    """Build one graph record while retaining an actionable structured issue."""
    try:
        return _build_raw_model(catalog, kind, record_id)
    except EvalLoadError as error:
        document = catalog.records[kind].get(record_id)
        issues.append(
            ValidationIssue(
                code=f"invalid_{kind[:-1]}",
                message=str(error),
                path=str(document.path) if document else None,
                asset_id=record_id,
            )
        )
        return None


def load_assets(evals_dir: Path | str = "evals") -> EvalAssets:
    """Load and validate the complete eval catalog in deterministic order.

    Full-catalog validation is useful for repository-wide maintenance checks.

    Args:
        evals_dir: Root directory containing all four asset directories.

    Returns:
        Fully model-validated assets indexed by stable ID.

    Raises:
        EvalLoadError: If any directory, TOML document, model, or ID is invalid.

    Example:
        >>> assets = load_assets("evals")
        >>> sorted(assets.suites)
        ['core', 'smoke']
    """
    root = Path(evals_dir)
    return EvalAssets(
        fixtures=_load_kind(root, "fixtures"),
        rubrics=_load_kind(root, "rubrics"),
        cases=_load_kind(root, "cases"),
        suites=_load_kind(root, "suites"),
    )


def load_suite_assets(
    evals_dir: Path | str = "evals",
    suite_id: str = "smoke",
    *,
    strict: bool = True,
) -> tuple[EvalAssets, EvalSuite]:
    """Load only the selected suite's transitive asset graph.

    Raw TOML is discovered globally so malformed files and duplicate IDs remain
    actionable, but Pydantic validation is limited to the selected suite and
    the core suite needed to enforce the smoke subset rule.

    Args:
        evals_dir: Root directory containing eval assets.
        suite_id: Stable ID of the suite to load.
        strict: Raise one combined load exception when graph issues exist. Set
            false when the caller will merge structured issues into a report.

    Returns:
        Partial or complete assets plus the selected, valid suite record.

    Raises:
        EvalLoadError: If discovery fails, the selected suite is invalid, or
            strict loading encounters transitive graph issues.

    Example:
        >>> assets, suite = load_suite_assets("evals", "smoke")
        >>> suite.id
        'smoke'
    """
    catalog = _discover_raw_catalog(evals_dir)
    raw_suite = catalog.records["suites"].get(suite_id)
    if raw_suite is None:
        available = ", ".join(sorted(catalog.records["suites"])) or "none"
        raise EvalLoadError(
            f"unknown suite '{suite_id}'; available suites: {available}"
        )

    suite = _build_raw_model(catalog, "suites", suite_id)
    suites = {suite.id: suite}
    issues: list[ValidationIssue] = []
    if suite.suite_kind == "smoke" or suite.id == "smoke":
        if "core" not in catalog.records["suites"]:
            issues.append(
                ValidationIssue(
                    code="missing_core_suite",
                    message="smoke validation requires a core suite",
                    asset_id="core",
                )
            )
        else:
            core = _try_build_raw_model(catalog, "suites", "core", issues)
            if core is not None:
                suites["core"] = core

    cases: dict[str, EvalCase] = {}
    fixtures: dict[str, EvalFixture] = {}
    rubrics: dict[str, EvalRubric] = {}
    attempted_fixtures: set[str] = set()
    attempted_rubrics: set[str] = set()
    for case_id in suite.case_ids:
        case = _try_build_raw_model(catalog, "cases", case_id, issues)
        if case is None:
            continue
        cases[case.id] = case
        if case.fixture_id not in attempted_fixtures:
            attempted_fixtures.add(case.fixture_id)
            fixture = _try_build_raw_model(catalog, "fixtures", case.fixture_id, issues)
            if fixture is not None:
                fixtures[fixture.id] = fixture
        if case.rubric_id not in attempted_rubrics:
            attempted_rubrics.add(case.rubric_id)
            rubric = _try_build_raw_model(catalog, "rubrics", case.rubric_id, issues)
            if rubric is not None:
                rubrics[rubric.id] = rubric

    assets = EvalAssets(fixtures, rubrics, cases, suites, tuple(issues))
    if strict and issues:
        raise EvalLoadError("; ".join(issue.render() for issue in issues))
    return assets, suite
