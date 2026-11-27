"""Private, content-addressed inputs for judging saved candidates."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from gmuse.commit import GenerationContext

from .inspect_adapter import stable_asset_digest
from .results import ResolvedCase

SCORING_EVIDENCE_DIRECTORY = ".gmuse-evidence"
_EVIDENCE_VERSION = 1
_SOURCE_RUN_FIELDS = (
    "run_id",
    "suite_id",
    "suite_version",
    "gmuse_eval_schema_version",
)
_SOURCE_SAMPLE_FIELDS = (
    "entry_id",
    "case_id",
    "case_revision",
    "fixture_id",
    "fixture_revision",
    "fixture_digest",
    "rubric_id",
    "rubric_version",
    "candidate_model",
    "candidate_kind",
    "generation_config",
    "prompt_sha256",
)


class ScoringEvidenceError(ValueError):
    """Evidence is missing, invalid, or incompatible with its source sample."""

    def __init__(self, reason: str) -> None:
        """Set a stable, safe reason to include in scoring metadata."""
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True, slots=True)
class VerifiedScoringEvidence:
    """Verified judge inputs and their Inspect-safe provenance."""

    staged_diff: str
    context: dict[str, Any]
    reference: dict[str, object]
    rubric_identity: dict[str, object]
    scoring_profile_identity: dict[str, object]


def _json_bytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _check_private(path: Path, *, directory: bool) -> None:
    details = path.lstat()
    expected_type = stat.S_ISDIR if directory else stat.S_ISREG
    if not expected_type(details.st_mode) or (
        os.name == "posix"
        and (details.st_uid != os.geteuid() or details.st_mode & 0o077)
    ):
        raise OSError("Evidence storage requires private, owner-controlled paths.")


def store_private_evidence(directory: Path, payload: bytes) -> str:
    """Write exact bytes to a private file named for their lowercase SHA-256.

    Args:
        directory: Dedicated evidence directory beneath an existing task path.
        payload: Bytes to store exactly as given.

    Returns:
        The SHA-256 digest, which is also the file name.

    Raises:
        OSError: If a private file cannot be published or verified.
    """
    directory.mkdir(mode=0o700, exist_ok=True)
    _check_private(directory, directory=True)
    digest = _digest(payload)
    destination = directory / digest
    temporary_path = None
    try:
        with NamedTemporaryFile(dir=directory, delete=False) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(payload)
        try:
            destination.hardlink_to(temporary_path)
        except FileExistsError:
            _check_private(destination, directory=False)
            if destination.read_bytes() != payload:
                raise OSError("Existing evidence does not match its digest.") from None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    return digest


def read_private_evidence(directory: Path, digest: str) -> bytes:
    """Read privately stored bytes and check that they match their SHA-256.

    Args:
        directory: Private directory that contains the requested evidence.
        digest: Lowercase SHA-256 file name.

    Returns:
        Exact verified bytes.

    Raises:
        ValueError: If the digest is malformed or the bytes do not match it.
        OSError: If the file cannot be read or is not private.
    """
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Invalid evidence digest.")
    _check_private(directory, directory=True)
    path = directory / digest
    _check_private(path, directory=False)
    stored = path.read_bytes()
    if _digest(stored) != digest:
        raise ValueError("Evidence does not match its digest.")
    return stored


def _asset_identities(
    case: ResolvedCase,
) -> tuple[dict[str, object], dict[str, object]]:
    rubric, profile = case.rubric, case.scoring_profile
    return (
        {
            "id": rubric.id,
            "revision": rubric.revision,
            "digest": stable_asset_digest(rubric),
        },
        {
            "id": profile.id,
            "revision": profile.revision,
            "digest": stable_asset_digest(profile),
        },
    )


def _source_identity(
    run: Mapping[str, object], sample: Mapping[str, object]
) -> dict[str, object]:
    message = sample.get("generated_message")
    return {
        **{key: run.get(key) for key in _SOURCE_RUN_FIELDS},
        **{key: sample.get(key) for key in _SOURCE_SAMPLE_FIELDS},
        "generated_message_sha256": (
            _digest(message.encode("utf-8")) if isinstance(message, str) else None
        ),
    }


def _used_context(context: GenerationContext, user_hint: str | None) -> dict[str, Any]:
    """Project the context onto the fields used by the production prompt."""
    data: dict[str, Any] = {}
    if context.history and context.history.commits:
        data["history"] = [record.message for record in context.history.commits[:5]]
    if context.branch_info:
        branch = {
            "type": context.branch_info.branch_type,
            "summary": context.branch_info.branch_summary,
        }
        data["branch"] = {key: value for key, value in branch.items() if value}
    instructions = context.repo_instructions
    if instructions and instructions.exists and instructions.content:
        data["repository_instructions"] = instructions.content
    if user_hint:
        data["user_hint"] = user_hint
    return data


def capture_scoring_evidence(
    log_dir: Path,
    run_metadata: Mapping[str, object],
    sample_metadata: Mapping[str, object],
    resolved_case: ResolvedCase,
    *,
    staged_diff: str,
    context: GenerationContext,
    user_hint: str | None,
) -> dict[str, object]:
    """Store exact judge evidence and return its public digest reference.

    Args:
        log_dir: Run log directory containing the adjacent private store.
        run_metadata: Source run identity.
        sample_metadata: Source sample identity and generation parameters.
        resolved_case: Validated source case with its rubric and profile.
        staged_diff: Full, canonical staged diff before prompt truncation.
        context: Context used to generate the candidate.
        user_hint: Hint used to generate the candidate, if any.

    Returns:
        A dictionary with a relative locator and SHA-256 digests for Inspect metadata.

    Raises:
        OSError: If the staged diff disagrees with its recorded digest or the
            private evidence cannot be written.
    """
    diff_digest = _digest(staged_diff.encode("utf-8"))
    if diff_digest != sample_metadata.get("staged_diff_digest"):
        raise OSError("Canonical diff does not match the recorded staged diff.")
    data = _used_context(context, user_hint)
    rubric_identity, profile_identity = _asset_identities(resolved_case)
    payload = _json_bytes(
        {
            "source": _source_identity(run_metadata, sample_metadata),
            "staged_diff": staged_diff,
            "context": data,
            "rubric_identity": rubric_identity,
            "scoring_profile_identity": profile_identity,
        }
    )
    digest = store_private_evidence(log_dir / SCORING_EVIDENCE_DIRECTORY, payload)
    return {
        "schema_version": _EVIDENCE_VERSION,
        "locator": f"{SCORING_EVIDENCE_DIRECTORY}/{digest}",
        "sha256": digest,
        "staged_diff_sha256": diff_digest,
        "context_sha256": _digest(_json_bytes(data)),
    }


def recover_scoring_evidence(
    source_log: Path,
    sample_metadata: Mapping[str, object],
    run_metadata: Mapping[str, object],
    resolved_case: ResolvedCase,
) -> VerifiedScoringEvidence:
    """Recover and verify the exact judge inputs associated with one candidate.

    Args:
        source_log: Path of the source candidate log.
        sample_metadata: Source sample's original metadata.
        run_metadata: Source runner metadata.
        resolved_case: Current validated case whose rubric and profile will be used.

    Returns:
        Verified exact inputs, source evidence reference, and asset identities.

    Raises:
        ScoringEvidenceError: If the source inputs could not be verified.
    """
    ref = sample_metadata.get("assessment_evidence_ref")
    if ref is None:
        raise ScoringEvidenceError("missing_assessment_evidence")
    if not isinstance(ref, dict) or ref.get("schema_version") != _EVIDENCE_VERSION:
        raise ScoringEvidenceError("invalid_assessment_evidence")
    digest = ref.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ScoringEvidenceError("invalid_assessment_evidence")
    if ref.get("locator") != f"{SCORING_EVIDENCE_DIRECTORY}/{digest}":
        raise ScoringEvidenceError("invalid_assessment_evidence")
    try:
        evidence_dir = source_log.resolve().parent / SCORING_EVIDENCE_DIRECTORY
        stored = read_private_evidence(evidence_dir, digest)
    except FileNotFoundError as error:
        raise ScoringEvidenceError("missing_assessment_evidence") from error
    except (OSError, RuntimeError, ValueError) as error:
        raise ScoringEvidenceError("invalid_assessment_evidence") from error
    try:
        payload = json.loads(stored)
        staged_diff = payload["staged_diff"]
        context = payload["context"]
        if not isinstance(staged_diff, str) or not isinstance(context, dict):
            raise TypeError
        diff_digest = _digest(staged_diff.encode("utf-8"))
        context_digest = _digest(_json_bytes(context))
    except (KeyError, TypeError, ValueError) as error:
        raise ScoringEvidenceError("invalid_assessment_evidence") from error
    if (
        ref.get("staged_diff_sha256") != diff_digest
        or ref.get("context_sha256") != context_digest
    ):
        raise ScoringEvidenceError("invalid_assessment_evidence")
    rubric_identity, profile_identity = _asset_identities(resolved_case)
    if (
        diff_digest != sample_metadata.get("staged_diff_digest")
        or diff_digest != resolved_case.fixture.expected_staged_diff_sha256
        or sample_metadata.get("case_id") != resolved_case.case.id
        or sample_metadata.get("case_revision") != resolved_case.case.revision
        or sample_metadata.get("fixture_id") != resolved_case.fixture.id
        or sample_metadata.get("fixture_revision") != resolved_case.fixture.revision
        or payload.get("source") != _source_identity(run_metadata, sample_metadata)
        or payload.get("rubric_identity") != rubric_identity
        or payload.get("scoring_profile_identity") != profile_identity
    ):
        raise ScoringEvidenceError("incompatible_assessment_evidence")
    return VerifiedScoringEvidence(
        staged_diff=staged_diff,
        context=context,
        reference={
            "schema_version": _EVIDENCE_VERSION,
            "locator": f"{SCORING_EVIDENCE_DIRECTORY}/{digest}",
            "sha256": digest,
            "staged_diff_sha256": diff_digest,
            "context_sha256": context_digest,
        },
        rubric_identity=rubric_identity,
        scoring_profile_identity=profile_identity,
    )
