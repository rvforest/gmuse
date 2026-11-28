"""Exact private judging evidence from real Inspect runner samples."""

from __future__ import annotations

import os
import stat
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import pytest
from inspect_ai.log import read_eval_log

from tools.evals.gmuse_evals.git_reconstruct import reconstruct_fixture
from tools.evals.gmuse_evals.inspect_adapter import stable_asset_digest
from tools.evals.gmuse_evals.inspect_runner import run_inspect_plan
from tools.evals.gmuse_evals.results import ResolvedCase
from tools.evals.gmuse_evals.run_plan import Guardrails, build_run_plan
from tools.evals.gmuse_evals.scoring_evidence import (
    ScoringEvidenceError,
    read_private_evidence,
    recover_scoring_evidence,
    store_private_evidence,
)
from tools.evals.gmuse_evals.validate import validate_suite

_ASSETS = Path(__file__).resolve().parents[2] / "evals"
_HINT = "Describe the guide without echoing this private hint."
_INSTRUCTIONS = "These private repository instructions should remain off the log."


@pytest.fixture(scope="module")
def candidate(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, dict[str, Any], dict[str, Any], ResolvedCase]:
    validated = validate_suite(_ASSETS, "smoke")
    plan = build_run_plan(
        validated,
        mode="check",
        guardrails=Guardrails(max_samples=1),
        overrides={
            "hint": _HINT,
            "repository_instructions": _INSTRUCTIONS,
            "max_diff_bytes": 64,
        },
    )
    run = run_inspect_plan(plan, log_dir=tmp_path_factory.mktemp("candidate-logs"))
    source = Path(run.logs[0].location)
    with source.open("rb") as stream:
        log = read_eval_log(stream)
    assert log.samples is not None
    return source, log.samples[0].metadata, log.metadata, plan.entries[0].resolved_case


@pytest.fixture
def evidence_file(
    candidate: tuple[Path, dict[str, Any], dict[str, Any], ResolvedCase],
) -> Iterator[Path]:
    source, sample, _, _ = candidate
    path = source.parent / sample["assessment_evidence_ref"]["locator"]
    before = path.read_bytes()
    yield path
    path.write_bytes(before)
    if os.name == "posix":
        path.chmod(0o600)


def test_round_trip_exact_evidence_without_raw_inputs_in_log(
    candidate: tuple[Path, dict[str, Any], dict[str, Any], ResolvedCase],
    evidence_file: Path,
) -> None:
    source, sample, run, case = candidate
    evidence = recover_scoring_evidence(source, sample, run, case)

    with reconstruct_fixture(case.fixture) as repo:
        assert evidence.staged_diff == repo.staged_diff.raw_diff
    assert len(evidence.staged_diff.encode("utf-8")) > 64
    assert evidence.context == {
        "branch": {"type": "feature", "summary": "docs/history"},
        "history": ["docs: establish eval fixture guide"],
        "repository_instructions": _INSTRUCTIONS,
        "user_hint": _HINT,
    }
    assert evidence.reference == sample["assessment_evidence_ref"]
    assert evidence.reference["staged_diff_sha256"] == sample["staged_diff_digest"]
    assert evidence.rubric_identity == {
        "id": case.rubric.id,
        "revision": case.rubric.revision,
        "digest": stable_asset_digest(case.rubric),
    }
    assert evidence.scoring_profile_identity == {
        "id": case.scoring_profile.id,
        "revision": case.scoring_profile.revision,
        "digest": stable_asset_digest(case.scoring_profile),
    }
    if os.name == "posix":
        assert stat.S_IMODE(evidence_file.parent.stat().st_mode) == 0o700
        assert stat.S_IMODE(evidence_file.stat().st_mode) == 0o600

    with ZipFile(source) as archived_log:
        contents = b"".join(archived_log.read(name) for name in archived_log.namelist())
    for raw in (
        _HINT,
        _INSTRUCTIONS,
        "docs: establish eval fixture guide",
        "diff --git",
    ):
        assert raw.encode("utf-8") not in contents


@pytest.mark.parametrize(
    ("alteration", "reason"),
    [
        ("deleted", "missing_assessment_evidence"),
        ("edited", "invalid_assessment_evidence"),
        ("reference_removed", "missing_assessment_evidence"),
        ("wrong_run", "incompatible_assessment_evidence"),
        ("wrong_output", "incompatible_assessment_evidence"),
        ("rubric_edited", "incompatible_assessment_evidence"),
        ("profile_edited", "incompatible_assessment_evidence"),
    ],
)
def test_missing_or_changed_evidence_cannot_be_judged(
    candidate: tuple[Path, dict[str, Any], dict[str, Any], ResolvedCase],
    evidence_file: Path,
    alteration: str,
    reason: str,
) -> None:
    source, original_sample, original_run, case = candidate
    sample, run = original_sample.copy(), original_run.copy()
    if alteration == "deleted":
        evidence_file.unlink()
    elif alteration == "edited":
        evidence_file.write_bytes(evidence_file.read_bytes() + b"\n")
    elif alteration == "reference_removed":
        sample.pop("assessment_evidence_ref")
    elif alteration == "wrong_run":
        run["run_id"] = "another-run"
    elif alteration == "wrong_output":
        sample["generated_message"] = "A different candidate message"
    elif alteration == "rubric_edited":
        case = replace(
            case, rubric=case.rubric.model_copy(update={"notes": "New notes"})
        )
    else:
        case = replace(
            case,
            scoring_profile=case.scoring_profile.model_copy(update={"dimensions": []}),
        )

    with pytest.raises(ScoringEvidenceError) as failure:
        recover_scoring_evidence(source, sample, run, case)

    assert failure.value.reason == reason


def test_content_addressed_storage_refuses_to_replace_modified_evidence(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "private"
    payload = b"exact bytes"
    digest = store_private_evidence(directory, payload)
    assert store_private_evidence(directory, payload) == digest
    assert read_private_evidence(directory, digest) == payload
    path = directory / digest
    path.write_bytes(b"changed bytes")
    with pytest.raises(OSError, match="does not match"):
        store_private_evidence(directory, payload)
    with pytest.raises(ValueError, match="does not match"):
        read_private_evidence(directory, digest)
    assert path.read_bytes() == b"changed bytes"


def test_candidate_log_survives_unavailable_private_storage(tmp_path: Path) -> None:
    log_dir = tmp_path / "candidate"
    log_dir.mkdir()
    (log_dir / ".gmuse-evidence").write_text("not an evidence directory")
    plan = build_run_plan(
        validate_suite(_ASSETS, "smoke"),
        mode="check",
        guardrails=Guardrails(max_samples=1),
    )

    run = run_inspect_plan(plan, log_dir=log_dir)

    (sample,) = run.results
    assert sample["generated_message"]
    assert sample["operational_error"] is None
    assert sample["assessment_evidence_error"] == "evidence_storage_unavailable"
    assert "assessment_evidence_ref" not in sample
