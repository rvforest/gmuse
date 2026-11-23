"""Domain rules for resolved eval assets."""

from __future__ import annotations

import re
from pathlib import PurePosixPath
from urllib.parse import urlparse

from license_expression import Licensing, get_spdx_licensing

from .composition import resolved_history_depth
from .git_reconstruct import ReconstructionError, reconstruct_fixture
from .models import (
    INJECTION_LOCATION_TAGS,
    INJECTION_PATTERN_TAGS,
    INJECTION_TAGS,
    SUPPORTED_ERROR_CATEGORIES,
    EvalFixture,
    ScoringProfile,
    ValidationIssue,
)
from .results import ResolvedCase

_FULL_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
_SECRET_LIKE = re.compile(
    r"(?:sk-[A-Za-z0-9]{8,}|api[_-]?key\s*[=:]|password\s*[=:])", re.I
)


def _issue(code: str, message: str, asset_id: str) -> ValidationIssue:
    return ValidationIssue(code=code, asset_id=asset_id, message=message)


def validate_provenance(fixture: EvalFixture) -> list[ValidationIssue]:
    """Validate origin-specific attribution without claiming legal approval.

    Example:
        >>> validate_provenance(fixture)
        []
    """
    provenance = fixture.provenance
    errors: list[ValidationIssue] = []
    if fixture.origin == "synthetic":
        if not provenance.synthetic_notes or not provenance.synthetic_notes.strip():
            errors.append(
                _issue(
                    "missing_synthetic_notes",
                    "missing provenance.synthetic_notes",
                    fixture.id,
                )
            )
        source_fields = (
            provenance.source_repository_url,
            provenance.source_owner_repo,
            provenance.source_commit_sha,
            provenance.source_commit_url,
            provenance.original_commit_message,
        )
        if any(source_fields):
            errors.append(
                _issue(
                    "synthetic_source_metadata",
                    "synthetic fixtures must not claim an external source commit",
                    fixture.id,
                )
            )
        return errors

    required = {
        "source_repository_url": provenance.source_repository_url,
        "source_owner_repo": provenance.source_owner_repo,
        "source_commit_sha": provenance.source_commit_sha,
        "source_commit_url": provenance.source_commit_url,
        "original_commit_message": provenance.original_commit_message,
        "imported_at": provenance.imported_at,
        "redistribution_review": provenance.redistribution_review,
    }
    for field_name, value in required.items():
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(
                _issue(
                    "missing_provenance",
                    f"missing provenance.{field_name}",
                    fixture.id,
                )
            )

    if provenance.source_commit_sha and not _FULL_SHA.fullmatch(
        provenance.source_commit_sha
    ):
        errors.append(
            _issue(
                "short_commit_sha",
                "provenance.source_commit_sha must be a full 40-character SHA",
                fixture.id,
            )
        )
    for field_name in ("source_repository_url", "source_commit_url"):
        value = getattr(provenance, field_name)
        if value and not _is_http_url(value):
            errors.append(
                _issue(
                    "invalid_source_url",
                    f"provenance.{field_name} must be an absolute HTTP(S) URL",
                    fixture.id,
                )
            )

    if not (provenance.source_license_expression or provenance.source_license_url):
        errors.append(
            _issue(
                "missing_license_evidence",
                "missing provenance.source_license_expression or provenance.source_license_url",
                fixture.id,
            )
        )
    if provenance.source_license_url is not None and not _is_license_reference(
        provenance.source_license_url
    ):
        errors.append(
            _issue(
                "invalid_license_reference",
                "provenance.source_license_url must be an absolute HTTP(S) URL "
                "or a safe repository-relative path",
                fixture.id,
            )
        )
    if provenance.source_license_expression and not _is_spdx_expression(
        provenance.source_license_expression
    ):
        errors.append(
            _issue(
                "invalid_license_expression",
                "provenance.source_license_expression is not a valid SPDX expression",
                fixture.id,
            )
        )
    if fixture.origin == "adapted" and not (
        provenance.adaptation_notes and provenance.adaptation_notes.strip()
    ):
        errors.append(
            _issue(
                "missing_adaptation_notes",
                "missing provenance.adaptation_notes",
                fixture.id,
            )
        )
    return errors


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_license_reference(value: str) -> bool:
    if not value.strip() or value != value.strip():
        return False
    parsed = urlparse(value)
    if parsed.scheme:
        return _is_http_url(value)
    if "\\" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute() and value not in {".", ".."} and ".." not in path.parts
    )


def _is_spdx_expression(value: str) -> bool:
    """Validate SPDX syntax while permitting document-local LicenseRef names."""
    try:
        references = re.findall(r"\bLicenseRef-[A-Za-z0-9.-]+\b", value)
        spdx = get_spdx_licensing()
        licensing = Licensing(symbols=[*spdx.known_symbols.values(), *references])
        return not licensing.validate(value).errors
    except Exception:
        # The third-party parser can surface non-domain exceptions for malformed
        # input; validation should report invalid evidence rather than crash.
        return False


def validate_safety(item: ResolvedCase) -> list[ValidationIssue]:
    """Validate injection taxonomy and nonfunctional secret-like test data.

    Example:
        >>> validate_safety(resolved_case)
        []
    """
    fixture = item.fixture
    errors: list[ValidationIssue] = []
    is_injection = "injection" in fixture.safety_tags
    if is_injection and not fixture.injection_tags:
        errors.append(
            _issue(
                "missing_injection_tags",
                "injection safety tag requires injection sub-tags",
                fixture.id,
            )
        )
    unknown = set(fixture.injection_tags).difference(INJECTION_TAGS)
    if unknown:
        errors.append(
            _issue(
                "unknown_injection_tags",
                f"unknown injection tags: {sorted(unknown)}",
                fixture.id,
            )
        )
    if fixture.injection_tags and not is_injection:
        errors.append(
            _issue(
                "orphan_injection_tags",
                "injection sub-tags require the 'injection' safety tag",
                fixture.id,
            )
        )
    if is_injection and fixture.injection_tags:
        tags = set(fixture.injection_tags)
        if not tags.intersection(INJECTION_PATTERN_TAGS):
            errors.append(
                _issue(
                    "missing_injection_pattern",
                    "injection fixtures require a recognized pattern tag",
                    fixture.id,
                )
            )
        if not tags.intersection(INJECTION_LOCATION_TAGS):
            errors.append(
                _issue(
                    "missing_injection_location",
                    "injection fixtures require a recognized location tag",
                    fixture.id,
                )
            )

    fixture_text = "\n".join(file.content for file in fixture.base_files)
    fixture_text += fixture.patch
    safety_text = " ".join(
        value or ""
        for value in (
            fixture.provenance.synthetic_notes,
            fixture.provenance.adaptation_notes,
            item.rubric.safety_notes,
        )
    ).lower()
    if _SECRET_LIKE.search(fixture_text) and not any(
        marker in safety_text
        for marker in ("fake", "nonfunctional", "non-functional", "test data")
    ):
        errors.append(
            _issue(
                "functional_secret_like_data",
                "secret-like test data must be marked fake or nonfunctional",
                fixture.id,
            )
        )
    if fixture.safety_tags and not item.rubric.safety_notes:
        errors.append(
            _issue(
                "missing_safety_notes",
                "safety-tagged fixtures require rubric safety_notes",
                fixture.id,
            )
        )
    return errors


def validate_history(item: ResolvedCase) -> list[ValidationIssue]:
    """Ensure requested commit history exists in the fixture.

    Example:
        >>> validate_history(resolved_case)
        []
    """
    depth = resolved_history_depth(item.case)
    if depth <= len(item.fixture.history):
        return []
    return [
        _issue(
            "history_depth_exceeds_fixture",
            f"resolved history_depth {depth} exceeds declared fixture history "
            f"length {len(item.fixture.history)}",
            item.case.id,
        )
    ]


def validate_profile(profile: ScoringProfile) -> list[ValidationIssue]:
    """Validate profile semantics that span nested records.

    Example:
        >>> validate_profile(profile)
        []
    """
    messages = [example.message for example in profile.usability_examples]
    if len(messages) == len(set(messages)):
        return []
    return [
        _issue(
            "duplicate_usability_examples",
            "profile usability examples must have distinct messages",
            profile.id,
        )
    ]


def validate_rubric(item: ResolvedCase) -> list[ValidationIssue]:
    """Validate one case rubric against its scoring profile and context.

    Example:
        >>> validate_rubric(resolved_case)
        []
    """
    rubric = item.rubric
    profile = item.scoring_profile
    errors: list[ValidationIssue] = []
    dimensions = {dimension.id for dimension in profile.dimensions}
    failure_severity = {
        condition.id: condition.severity for condition in rubric.failure_conditions
    }
    failure_ids = set(failure_severity)
    gate_ids = {gate.id for gate in rubric.deterministic_gates}

    for criterion in rubric.criteria:
        if criterion.dimension not in dimensions:
            errors.append(
                _issue(
                    "unknown_rubric_dimension",
                    f"criterion {criterion.id} references unknown profile dimension "
                    f"'{criterion.dimension}'",
                    rubric.id,
                )
            )
    for condition in rubric.failure_conditions:
        if condition.error_category not in SUPPORTED_ERROR_CATEGORIES:
            errors.append(
                _issue(
                    "unsupported_error_category",
                    f"failure condition {condition.id} uses unsupported error category "
                    f"'{condition.error_category}'",
                    rubric.id,
                )
            )

    usable_examples = [
        example for example in rubric.examples if example.usability == "usable"
    ]
    if len(usable_examples) != 1:
        errors.append(
            _issue(
                "usable_example_count",
                "rubric requires exactly one usable example",
                rubric.id,
            )
        )

    for index, example in enumerate(rubric.examples, start=1):
        unknown_dimensions = set(example.ratings).difference(dimensions)
        if unknown_dimensions:
            errors.append(
                _issue(
                    "unknown_example_dimension",
                    f"example {index} references unknown dimensions: "
                    f"{sorted(unknown_dimensions)}",
                    rubric.id,
                )
            )
        invalid_ratings = {
            dimension: rating
            for dimension, rating in example.ratings.items()
            if dimension in dimensions and rating not in {1, 2, 3, 4}
        }
        if invalid_ratings:
            errors.append(
                _issue(
                    "invalid_example_rating",
                    f"example {index} ratings must use anchors 1 through 4: "
                    f"{invalid_ratings}",
                    rubric.id,
                )
            )
        unknown_gates = set(example.expected_gate_ids).difference(gate_ids)
        if unknown_gates:
            errors.append(
                _issue(
                    "unknown_example_gate",
                    f"example {index} references unknown gate(s): {sorted(unknown_gates)}",
                    rubric.id,
                )
            )
        unknown_failures = set(example.expected_failure_ids).difference(failure_ids)
        if unknown_failures:
            errors.append(
                _issue(
                    "unknown_example_failure",
                    f"example {index} references unknown failure condition(s): "
                    f"{sorted(unknown_failures)}",
                    rubric.id,
                )
            )
        if example.expected_gate_ids and example.usability != "unusable":
            errors.append(
                _issue(
                    "failed_gate_requires_unusable",
                    f"example {index} fails a deterministic gate and must be unusable",
                    rubric.id,
                )
            )
        if example.usability == "usable" and example.expected_failure_ids:
            errors.append(
                _issue(
                    "usable_example_has_failure",
                    f"example {index} is usable but declares a failure condition",
                    rubric.id,
                )
            )

    failure_example = next(
        (example for example in rubric.examples if example.usability != "usable"),
        None,
    )
    has_major_failure = bool(
        failure_example
        and any(
            failure_severity.get(failure_id) == "major"
            for failure_id in failure_example.expected_failure_ids
        )
    )
    has_failed_gate = bool(failure_example and failure_example.expected_gate_ids)
    if not has_major_failure and not has_failed_gate:
        errors.append(
            _issue(
                "missing_failure_example",
                "rubric needs a major failure or failed deterministic-gate example",
                rubric.id,
            )
        )

    gate_kinds = {gate.gate for gate in rubric.deterministic_gates}
    if "production_validation" not in gate_kinds:
        errors.append(
            _issue(
                "missing_production_validation_gate",
                "rubric must declare the production-validation gate",
                rubric.id,
            )
        )
    has_length_gate = "max_chars" in gate_kinds
    if item.case.max_chars is not None and not has_length_gate:
        errors.append(
            _issue(
                "missing_max_chars_gate",
                "case max_chars requires a matching deterministic gate",
                rubric.id,
            )
        )
    if item.case.max_chars is None and has_length_gate:
        errors.append(
            _issue(
                "inapplicable_max_chars_gate",
                "max_chars gate requires case max_chars to be configured",
                rubric.id,
            )
        )
    return errors


def validate_reconstruction(fixture: EvalFixture) -> list[ValidationIssue]:
    """Reconstruct a fixture and compare exact staged metadata.

    Example:
        >>> validate_reconstruction(fixture)
        []
    """
    try:
        with reconstruct_fixture(fixture) as repository:
            observed = repository.staged_diff
    except ReconstructionError as error:
        return [_issue("reconstruction_failed", str(error), fixture.id)]

    errors: list[ValidationIssue] = []
    if observed.hash != fixture.expected_staged_diff_sha256:
        errors.append(
            _issue(
                "digest_mismatch",
                "staged diff digest mismatch; "
                f"expected {fixture.expected_staged_diff_sha256}, observed {observed.hash}",
                fixture.id,
            )
        )
    observed_paths = sorted(observed.files_changed)
    if observed_paths != fixture.expected_files_changed:
        errors.append(
            _issue(
                "changed_paths_mismatch",
                f"changed paths mismatch; expected {fixture.expected_files_changed}, "
                f"observed {observed_paths}",
                fixture.id,
            )
        )
    return errors
