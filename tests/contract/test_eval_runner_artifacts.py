from __future__ import annotations

from tools.evals.gmuse_evals.logs import EVAL_SCHEMA_VERSION, build_run_metadata


def test_run_metadata_contract_has_required_versioned_fields() -> None:
    metadata = build_run_metadata(
        execution_mode="check",
        suite_id="smoke",
        suite_version="1.0",
        selected_case_ids=["case-1"],
        prompt_version="1.0.0",
    )
    for key in (
        "gmuse_eval_schema_version",
        "execution_mode",
        "suite_id",
        "suite_version",
        "selected_case_ids",
        "prompt_version",
    ):
        assert key in metadata
    assert metadata["gmuse_eval_schema_version"] == EVAL_SCHEMA_VERSION


def test_run_metadata_excludes_raw_context_overrides() -> None:
    metadata = build_run_metadata(
        execution_mode="check",
        suite_id="smoke",
        suite_version="1",
        selected_case_ids=["case-1"],
        prompt_version="1.0.0",
        effective_generation_defaults={
            "hint": "private hint",
            "repository_instructions": "private repository instructions",
            "max_chars": 80,
        },
    )

    assert metadata["effective_generation_defaults"] == {"max_chars": 80}
