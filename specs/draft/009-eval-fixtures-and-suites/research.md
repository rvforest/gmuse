# Research: Eval Fixtures And Suites

## Decision: Store fixtures as offline reconstruction data, not source clones

**Rationale**: Normal validation and later eval runs must be self-contained once
fixtures are checked in. Storing enough compact file and patch data to
reconstruct a temporary git repository lets evals exercise gmuse's real staged
diff machinery without requiring network access or source repository clones.

**Alternatives considered**:

- Clone source repositories during every run: rejected because it is slower,
  network-dependent, and unsuitable for default maintainer validation.
- Store only raw diffs without repository reconstruction data: rejected because
  later eval runner work needs production git behavior over staged changes.
- Store fully copied source repositories: rejected because it is too large and
  creates unnecessary licensing and review burden.

## Decision: Keep eval code and eval assets separate

**Rationale**: Evals are maintainer tooling, not ordinary gmuse application
functionality. The implementation code should live under `tools/evals/` while
reviewable fixture/rubric/case/suite TOML assets live under root `evals/`. This
keeps `src/gmuse` focused on the installed product while still allowing the
maintainer tool to import gmuse internals when fidelity requires it.

**Alternatives considered**:

- Put eval code under `src/gmuse/evals`: rejected because it makes draft
  maintainer tooling look like packaged product functionality.
- Put Python tooling directly inside `evals/`: rejected because it mixes code
  with declarative eval assets.
- Use a nox session as the primary interface: rejected for the first
  implementation because the module entrypoint should define the tool behavior;
  nox can be added later as a shortcut.

## Decision: Use TOML with Pydantic structural validation

**Rationale**: TOML is already part of gmuse's dependency set through
`tomli`/`tomllib` and `tomlkit`, and it avoids introducing YAML parsing.
Pydantic is already present transitively, but the implementation should add it
as an explicit development dependency before relying on it. Pydantic should
handle structural validation while custom validators handle eval-domain checks
such as references, smoke/core membership, digest verification, and conventional
type compatibility.

**Alternatives considered**:

- Hand-written schema validation only: rejected because nested fixture, rubric,
  case, and suite models would create avoidable boilerplate and inconsistent
  errors.
- Rely on transitive Pydantic only: rejected because transitive dependencies are
  not a stable contract for maintainer tooling.
- YAML: rejected because it would add a parser dependency and TOML is workable
  for multiline patch strings.

## Decision: Validate staged diff digests after reconstruction

**Rationale**: The fixture is only trustworthy if the temporary repository
produces the expected staged diff through git. Digest verification catches
schema errors, patch drift, path mistakes, line-ending issues, and accidental
fixture edits before live eval results depend on them. The digest should be
computed from the exact raw `git diff --cached` output observed by gmuse's
production staged-diff helper, with temp repo git settings chosen to reduce
platform variance.

**Alternatives considered**:

- Trust checked-in patch text: rejected because it does not prove production git
  extraction will observe the same diff.
- Compare normalized summaries only: rejected because eval accuracy depends on
  exact diff evidence, not just file counts.
- Automatically update stored digests in the first PR: rejected because it adds
  TOML mutation behavior before it is needed. The validator should print the
  observed digest for intentional fixture updates.

## Decision: Reconstruct synthetic history as real temporary commits

**Rationale**: Commit history is a core gmuse context source. Creating actual
synthetic commits in the temporary repository proves that future calls to
`gmuse.git.get_commit_history()` will observe realistic history. The first
schema only needs `subject` and optional `body`; deterministic author, email,
and timestamps can be supplied by the validator.

**Alternatives considered**:

- Validate history TOML without creating commits: rejected because it does not
  prove production git history behavior.
- Require full author/timestamp metadata in fixture history: rejected for the
  first implementation because gmuse currently consumes commit messages, not
  detailed history metadata.

## Decision: Use explicit provenance categories

**Rationale**: Real OSS commits, adapted fixtures, and synthetic safety cases
carry different attribution and review obligations. The schema should make the
origin kind explicit and validate only the metadata required for that origin.
External guidance supports this direction: NIST describes provenance metadata as
including origin, modification, and source information for data and generated
content, while Hugging Face dataset cards emphasize responsible-use context,
creation context, and known considerations for datasets
([NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf),
[Hugging Face dataset cards](https://huggingface.co/docs/datasets/dataset_card)).

**Alternatives considered**:

- Require source metadata for every fixture: rejected because synthetic privacy
  and injection cases may have no external source.
- Allow freeform provenance notes only: rejected because missing attribution
  would be hard to detect automatically.

## Decision: Record license evidence separately from redistribution approval

**Rationale**: SPDX license expressions provide a compact way to capture common
open source licensing terms, but eval fixture validation should not pretend to
perform legal review. Real and adapted fixtures should record an SPDX expression
or a source license URL plus a maintainer review status. This preserves evidence
for review and keeps validation honest about what it can prove
([SPDX license expressions](https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/)).

**Alternatives considered**:

- Store only a freeform license label: rejected because it is hard to compare or
  validate across fixtures.
- Require SPDX expressions for every source: rejected because some repositories
  may require a license reference or review note when the license is unclear.
- Treat license metadata as redistribution approval: rejected because metadata
  validation is not legal approval.

## Decision: Broaden injection safety tags beyond obvious text prompts

**Rationale**: OWASP distinguishes direct and indirect prompt injection and
notes obfuscated, encoded, and external-content patterns. gmuse's eval fixtures
should therefore tag where instruction-like content appears in a diff and what
kind of injection pattern it represents, rather than only testing plain
`ignore previous instructions` examples
([OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)).

**Alternatives considered**:

- Keep one generic `injection` tag: rejected because it hides coverage gaps.
- Defer injection categorization to judge scoring: rejected because fixture
  validation and coverage reporting need to know what safety behavior is being
  exercised before live runs.

## Decision: Treat suite balance as advisory by default

**Rationale**: Early eval suites should report coverage gaps without blocking
progress while the case set is small. Individual suite policies can later mark a
coverage rule required once the core set matures.

**Alternatives considered**:

- Fail every balance gap: rejected because the initial smoke suite is
  intentionally tiny.
- Skip coverage reporting until the core suite is complete: rejected because
  early reports help prevent accidental overrepresentation.

## Decision: Defer fixture importer automation

**Rationale**: Importer design depends on the final fixture schema. Manual
fixtures are enough to prove reconstruction, provenance validation, and suite
membership first.

**Alternatives considered**:

- Build importer before schemas settle: rejected because importer output would
  churn with schema changes.
- Exclude real OSS fixtures entirely: rejected because attribution requirements
  should be validated before broader eval work.

## Decision: Start with synthetic-only smoke fixtures

**Rationale**: The first implementation should prove schema loading, reference
resolution, temporary git reconstruction, synthetic history commits, digest
verification, and coverage reporting without spending scope on real OSS curation
or redistribution review. Two synthetic fixtures provide enough coverage: one
ordinary docs/history fixture and one injection-tagged fixture that exercises
safety metadata without testing model behavior.

**Alternatives considered**:

- Include one real OSS fixture immediately: rejected because source selection and
  redistribution review would slow the foundation PR.
- Use one fixture only: rejected because it would not exercise both ordinary
  history and safety metadata paths.

## Decision: Human-readable validation output first

**Rationale**: The first validator is a maintainer tool for local authoring and
review. It should return a structured internal `ValidationReport`, but the first
CLI surface only needs actionable text output. Machine-readable `--json` output
can be added once automation needs it.

**Alternatives considered**:

- Add `--json` immediately: rejected because it expands the public contract
  before the report schema has been exercised.
- Print only the first error: rejected because fixture authors need aggregated
  schema, reference, provenance, and digest issues.
