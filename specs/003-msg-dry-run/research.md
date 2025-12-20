# Phase 0 Research: `gmuse msg --dry-run`

## Decisions

### Decision 1 — Implement dry-run at the CLI layer

- Decision: Add `--dry-run` to `gmuse msg` and short-circuit before any provider client initialization.
- Rationale:
  - Prevents `gmuse.llm.LLMClient` from running provider detection or importing provider-specific behavior.
  - Keeps the public API surface stable (no need to add a new public parameter to `generate_message`).
  - Matches the spec’s requirement that dry-run is a CLI feature and must preserve CLI error handling.
- Alternatives considered:
  - Add a `dry_run` parameter to `gmuse.commit.generate_message`.
    - Rejected because it expands public API and can blur responsibilities (generation vs prompt preview).

### Decision 2 — Use existing prompt builder (`gmuse.prompts.build_prompt`) as the single source of truth

- Decision: Assemble `system_prompt` + `user_prompt` using `build_prompt(...)` with the same inputs as the normal generation path.
- Rationale:
  - Guarantees the printed prompts match what a real run would send.
  - Avoids drift caused by duplicating prompt construction.
- Alternatives considered:
  - Reconstruct prompt logic in CLI.
    - Rejected because it increases maintenance risk and reduces test confidence.

### Decision 3 — Output is plain text with a metadata header

- Decision: Print plain text output with this layout:

  ```
  MODEL: <model or none>
  FORMAT: <format>
  TRUNCATED: true|false

  SYSTEM PROMPT:
  <system_prompt>

  USER PROMPT:
  <user_prompt>
  ```

- Rationale:
  - Human-readable and easy to paste into issues or review.
  - Metadata makes dry-run output reproducible without changing the main payload.
- Alternatives considered:
  - JSON output.
    - Deferred by spec; could be added as a follow-up if automation needs arise.

### Decision 4 — Testing strategy: assert “no provider calls” directly

- Decision:
  - Unit tests will monkeypatch/mocking `gmuse.llm.LLMClient.generate` (or `LLMClient` construction) and assert it is not called.
  - Integration tests will execute the CLI and assert the output contains the metadata header and both prompts.
- Rationale:
  - Makes the core safety property explicit: dry-run must not contact providers.
- Alternatives considered:
  - Rely on absence of network calls.
    - Rejected because it is harder to assert deterministically in unit tests.

## Notes / Best-practice reminders

- Keep dry-run behavior as close as possible to normal prompt assembly: same config merge, same context gathering, same diff truncation behavior.
- Prefer a small helper function for formatting the output to keep `cli/main.py` readable and easily testable.
