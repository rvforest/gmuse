# Tasks: LLM-Powered Commit Message Generator

**Input**: Design documents from `/specs/001-llm-commit-messages/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/prompt-templates.md

**Feature Branch**: `001-llm-commit-messages`
**Date**: 2025-11-28

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [X] T001 Add dependencies to pyproject.toml: litellm (optional extra), pyperclip (optional extra), tomli (for Python 3.10)
- [X] T002 [P] Create tests/unit/ directory structure
- [X] T003 [P] Create tests/integration/ directory structure
- [X] T004 [P] Configure mypy strict mode for new modules in pyproject.toml
- [X] T005 [P] Update .pre-commit-config.yaml to include new src/gmuse/ modules in checks

**Checkpoint**: Project structure ready for implementation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Create src/gmuse/config.py with XDG path resolver (`get_config_path()`) per [plan.md § Step 1.1](plan.md#step-11-configuration-module)
- [X] T007 [P] Implement TOML config loader (`load_config()`) in src/gmuse/config.py with tomllib/tomli per [research.md § Configuration Management](research.md#3-configuration-management)
- [X] T008 [P] Implement config validator (`validate_config()`) in src/gmuse/config.py per [data-model.md § UserConfig validation](data-model.md#5-userconfig)
- [X] T009 [P] Implement config merger (`merge_config()`) in src/gmuse/config.py with priority: CLI > config.toml > env > defaults
- [X] T010 [P] Create src/gmuse/git_utils.py with repo validator (`is_git_repository()`) using `git rev-parse --git-dir` per [plan.md § Step 1.2](plan.md#step-12-git-utilities-module)
- [X] T011 [P] Implement repo root getter (`get_repo_root()`) in src/gmuse/git_utils.py using `git rev-parse --show-toplevel`
- [X] T012 [P] Implement staged diff extractor (`get_staged_diff()`) in src/gmuse/git_utils.py returning StagedDiff per [data-model.md § StagedDiff](data-model.md#2-stageddiff)
- [X] T013 [P] Implement commit history fetcher (`get_commit_history()`) in src/gmuse/git_utils.py returning CommitHistory per [data-model.md § CommitHistory](data-model.md#3-commithistory)
- [X] T014 [P] Implement diff truncator (`truncate_diff()`) in src/gmuse/git_utils.py per [research.md § Token Management Strategy](research.md#7-token-management-strategy)
- [X] T015 [P] Create src/gmuse/llm_client.py with provider detector (`detect_provider()`) checking OPENAI_API_KEY, ANTHROPIC_API_KEY per [plan.md § Step 1.3](plan.md#step-13-llm-client-module)
- [X] T016 [P] Implement model resolver (`resolve_model()`) in src/gmuse/llm_client.py per [research.md § LLM Provider Integration](research.md#1-llm-provider-integration)
- [X] T017 [P] Implement LLMClient class with `generate()` method in src/gmuse/llm_client.py using litellm.completion()
- [X] T018 [P] Implement availability checker (`is_llm_available()`) in src/gmuse/llm_client.py
- [X] T019 [P] Create src/gmuse/prompt_builder.py with SYSTEM_PROMPT constant per [contracts/prompt-templates.md § Base System Prompt](contracts/prompt-templates.md#base-system-prompt)
- [X] T020 [P] Implement context builder (`build_context()`) in src/gmuse/prompt_builder.py per [contracts/prompt-templates.md § Context Section Template](contracts/prompt-templates.md#context-section-template)
- [X] T021 [P] Implement task prompt getters in src/gmuse/prompt_builder.py: `get_freeform_task()`, `get_conventional_task()`, `get_gitmoji_task()` per [contracts/prompt-templates.md](contracts/prompt-templates.md)
- [X] T022 [P] Implement prompt assembler (`build_prompt()`) in src/gmuse/prompt_builder.py with token estimation and truncation
- [X] T023 [P] Implement message validator (`validate_message()`) in src/gmuse/prompt_builder.py per [data-model.md § CommitMessage validation](data-model.md#1-commitmessage)
- [X] T024 Add custom exceptions: `ConfigError`, `NotAGitRepositoryError`, `NoStagedChangesError`, `LLMError`, `InvalidMessageError` in src/gmuse/exceptions.py
- [X] T025 Add structured logging with `GMUSE_DEBUG` environment variable toggle in src/gmuse/logging.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Generate Basic Commit Message (Priority: P1) 🎯 MVP

**Goal**: Generate commit messages from staged changes with zero-config first-time use

**Independent Test**: Stage changes in a git repo, run `gmuse`, verify message is output to STDOUT

**Reference**: [spec.md § User Story 1](spec.md#user-story-1---generate-basic-commit-message-priority-p1)

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T026 [P] [US1] Create tests/unit/test_config.py with tests for XDG path resolution, TOML parsing, validation, priority merging per [plan.md § Step 1.1 Test](plan.md#step-11-configuration-module)
- [X] T027 [P] [US1] Create tests/unit/test_git_utils.py with tests for repo validation, diff extraction, history fetching, diff truncation per [plan.md § Step 1.2 Test](plan.md#step-12-git-utilities-module)
- [X] T028 [P] [US1] Create tests/unit/test_llm_client.py with tests for provider detection, model resolution, generation (mocked), availability check per [plan.md § Step 1.3 Test](plan.md#step-13-llm-client-module)
- [X] T029 [P] [US1] Create tests/unit/test_prompt_builder.py with tests for context building, task prompts, prompt assembly, message validation per [plan.md § Step 1.4 Test](plan.md#step-14-prompt-builder-module)
- [X] T030 [US1] Create tests/integration/test_cli.py with tests for all 5 P1 acceptance scenarios using temp git repos and mocked LLM per [plan.md § Step 1.5 Test](plan.md#step-15-cli-command)

### Implementation for User Story 1

- [X] T031 [US1] Add generate command to src/gmuse/cli/main.py with flags: `--hint`, `--copy`, `--model`, `--format`, `--history-depth` per [plan.md § UX Gate CLI Changes](plan.md#ux-gate-)
- [X] T032 [US1] Implement main flow in generate() function: load config, validate repo, get diff, get history, build prompt, call LLM, validate, output per [plan.md § Step 1.5](plan.md#step-15-cli-command)
- [X] T033 [US1] Add error handling with actionable messages per [plan.md § UX Gate Error Messages](plan.md#ux-gate-): "Not a git repository", "No staged changes", "No API key", network timeout, invalid config
- [X] T034 [US1] Add CLI help text with examples for each flag referencing [quickstart.md](quickstart.md)
- [X] T035 [US1] Set exit codes: 0=success, 1=user error, 2=system error
- [X] T036 [US1] Add logging for all CLI operations (config load, git ops, LLM calls, errors) with GMUSE_DEBUG support

**Acceptance Verification for US1**:
1. ✅ Given staged changes, when user runs `gmuse`, then message generated and printed to STDOUT
2. ✅ Given no staged changes, when user runs `gmuse`, then error "No staged changes found..."
3. ✅ Given not a git repo, when user runs `gmuse`, then error "Not a git repository..."
4. ✅ Given no API key, when user runs `gmuse`, then error "No API key configured..."
5. ✅ Given staged changes and valid API key, when user runs `gmuse`, then message reflects diff content

**Checkpoint**: User Story 1 complete - MVP functional! Can generate commit messages from staged changes.

---

## Phase 4: User Story 2 - Influence Message with Runtime Hints (Priority: P2)

**Goal**: Allow per-commit customization via `--hint` flag without persistent config

**Independent Test**: Run `gmuse --hint "focus on security"` and verify hint influences generated message

**Reference**: [spec.md § User Story 2](spec.md#user-story-2---influence-message-with-runtime-hints-priority-p2)

### Tests for User Story 2

- [ ] T037 [P] [US2] Add integration tests to tests/integration/test_cli.py for all 3 P2 acceptance scenarios with various hint values

### Implementation for User Story 2

- [ ] T038 [US2] Verify `--hint` flag is properly integrated into `build_context()` in src/gmuse/prompt_builder.py (should already work from Phase 2)
- [ ] T039 [US2] Add tests verifying hints are included in prompt context per [contracts/prompt-templates.md § Context Section](contracts/prompt-templates.md#context-section-template)
- [ ] T040 [US2] Update CLI help text in src/gmuse/cli/main.py with hint examples

**Acceptance Verification for US2**:
1. ✅ Given staged changes, when `gmuse --hint "emphasize performance"`, then message mentions performance
2. ✅ Given staged changes, when `gmuse --hint "breaking change"`, then message includes breaking change indicators
3. ✅ Given staged changes, when `gmuse` without hint, then message based on diff/history only

**Checkpoint**: User Story 2 complete - Hints working!

---

## Phase 5: User Story 3 - Copy Message to Clipboard (Priority: P2)

**Goal**: Auto-copy generated messages to clipboard for workflow efficiency

**Independent Test**: Run `gmuse --copy` and verify clipboard contains generated message

**Reference**: [spec.md § User Story 3](spec.md#user-story-3---copy-message-to-clipboard-priority-p2)

### Tests for User Story 3

- [ ] T041 [P] [US3] Add integration tests to tests/integration/test_cli.py for all 3 P2 acceptance scenarios with clipboard mocking

### Implementation for User Story 3

- [ ] T042 [P] [US3] Add pyperclip integration to src/gmuse/cli/main.py in generate() function with graceful degradation per [research.md § Clipboard Operations](research.md#4-clipboard-operations)
- [ ] T043 [US3] Handle clipboard unavailable with warning message (don't fail) per [spec.md § Edge Cases](spec.md#edge-cases)
- [ ] T044 [US3] Respect `copy_to_clipboard` config option from config.toml per [data-model.md § UserConfig](data-model.md#5-userconfig)
- [ ] T045 [US3] Update CLI help text with `--copy` flag description and examples

**Acceptance Verification for US3**:
1. ✅ Given clipboard available, when `gmuse --copy`, then message copied to clipboard and printed to STDOUT
2. ✅ Given clipboard unavailable, when `gmuse --copy`, then message printed with warning
3. ✅ Given `copy_to_clipboard = true` in config, when `gmuse`, then auto-copy

**Checkpoint**: User Story 3 complete - Clipboard support working!

---

## Phase 6: User Story 4 - Customize Message Format Style (Priority: P2)

**Goal**: Support conventional commits and gitmoji formats for team standards

**Independent Test**: Run `gmuse --format conventional` and verify output follows Conventional Commits format

**Reference**: [spec.md § User Story 4](spec.md#user-story-4---customize-message-format-style-priority-p2)

### Tests for User Story 4

- [ ] T046 [P] [US4] Add integration tests to tests/integration/test_cli.py for all 4 P2 acceptance scenarios with different format values
- [ ] T047 [P] [US4] Add unit tests to tests/unit/test_prompt_builder.py verifying format-specific validation (conventional regex, gitmoji emoji)

### Implementation for User Story 4

- [ ] T048 [US4] Verify format-specific task prompts work correctly in src/gmuse/prompt_builder.py (should already be implemented from Phase 2)
- [ ] T049 [US4] Verify format-specific validation in `validate_message()` works per [data-model.md § CommitMessage validation](data-model.md#1-commitmessage)
- [ ] T050 [US4] Respect `format` config option from config.toml with CLI override priority
- [ ] T051 [US4] Update CLI help text with `--format` flag description and examples for each format

**Acceptance Verification for US4**:
1. ✅ Given staged changes, when `gmuse --format conventional`, then message follows "type(scope): description" format
2. ✅ Given staged changes, when `gmuse --format gitmoji`, then message includes emoji prefix
3. ✅ Given staged changes, when `gmuse --format freeform`, then message has no formatting constraints
4. ✅ Given `format = "conventional"` in config, when `gmuse`, then conventional format used

**Checkpoint**: User Story 4 complete - Format styles working!

---

## Phase 7: User Story 5 - Repository-Level Instructions (Priority: P3)

**Goal**: Enable project-specific commit message guidance via `.gmuse` file

**Independent Test**: Create `.gmuse` file with "Always mention ticket numbers", run `gmuse`, verify instruction reflected

**Reference**: [spec.md § User Story 5](spec.md#user-story-5---repository-level-instructions-priority-p3)

### Tests for User Story 5

- [ ] T052 [P] [US5] Add unit tests to tests/unit/test_git_utils.py for `.gmuse` file loading (present, absent, empty)
- [ ] T053 [P] [US5] Add integration tests to tests/integration/test_cli.py for all 3 P3 acceptance scenarios with/without `.gmuse` file

### Implementation for User Story 5

- [ ] T054 [P] [US5] Add `.gmuse` file loader (`load_repository_instructions()`) to src/gmuse/git_utils.py returning RepositoryInstructions per [data-model.md § RepositoryInstructions](data-model.md#4-repositoryinstructions)
- [ ] T055 [US5] Integrate `.gmuse` loading into CLI flow in src/gmuse/cli/main.py before prompt building
- [ ] T056 [US5] Ensure `build_context()` includes repository instructions per [contracts/prompt-templates.md § Context Section](contracts/prompt-templates.md#context-section-template)
- [ ] T057 [US5] Verify hint takes precedence over `.gmuse` when both present per [data-model.md § UserConfig priority](data-model.md#priority-resolution)

**Acceptance Verification for US5**:
1. ✅ Given `.gmuse` with "Always reference issue numbers", when `gmuse`, then message attempts to reference issues
2. ✅ Given `.gmuse` and `--hint`, when `gmuse`, then both influence message with hint precedence
3. ✅ Given no `.gmuse`, when `gmuse`, then message generated without repo-specific instructions

**Checkpoint**: User Story 5 complete - Repository instructions working!

---

## Phase 8: User Story 6 - Global Configuration (Priority: P3)

**Goal**: Persistent user preferences via config.toml across all projects

**Independent Test**: Create config.toml with `copy_to_clipboard = true`, run `gmuse`, verify auto-copy behavior

**Reference**: [spec.md § User Story 6](spec.md#user-story-6---global-configuration-priority-p3)

### Tests for User Story 6

- [ ] T058 [P] [US6] Add integration tests to tests/integration/test_cli.py for all 4 P3 acceptance scenarios with various config.toml values

### Implementation for User Story 6

- [ ] T059 [US6] Verify all config options are properly loaded and applied in src/gmuse/cli/main.py (should already work from Phase 2)
- [ ] T060 [US6] Verify config validation handles all edge cases: invalid keys, out-of-range values, bad TOML syntax per [research.md § Configuration Management](research.md#3-configuration-management)
- [ ] T061 [US6] Verify defaults are used when config.toml doesn't exist per [data-model.md § UserConfig defaults](data-model.md#default-values)
- [ ] T062 [US6] Add clear error messages for config errors pointing to line/key per [plan.md § UX Gate](plan.md#ux-gate-)

**Acceptance Verification for US6**:
1. ✅ Given config with `copy_to_clipboard = true`, when `gmuse`, then auto-copy
2. ✅ Given config with `model = "gpt-4"`, when `gmuse`, then gpt-4 used
3. ✅ Given config with `history_depth = 10`, when `gmuse`, then 10 commits used
4. ✅ Given no config, when `gmuse`, then reasonable defaults (no copy, auto-detect model, 5 commits)

**Checkpoint**: User Story 6 complete - Global config working!

---

## Phase 9: User Story 7 - Learn from User Edits (Priority: P3)

**Goal**: Opt-in learning from user edits to improve message quality over time

**Independent Test**: Enable learning, provide edited messages, verify future messages use edits as examples

**Reference**: [spec.md § User Story 7](spec.md#user-story-7---learn-from-user-edits-priority-p3)

### Tests for User Story 7

- [ ] T063 [P] [US7] Create tests/unit/test_learning.py with tests for repo ID generation, record appending, history loading, few-shot formatting per [plan.md § Step 3.1 Test](plan.md#step-31-learning-module)
- [ ] T064 [P] [US7] Add integration tests to tests/integration/test_cli.py for all 4 P3 acceptance scenarios with learning enabled/disabled

### Implementation for User Story 7

- [ ] T065 [P] [US7] Create src/gmuse/learning.py with repo identifier (`get_repo_id()`) using SHA256 of repo root path per [data-model.md § LearningRecord](data-model.md#6-learningrecord)
- [ ] T066 [P] [US7] Implement record writer (`append_learning_record()`) in src/gmuse/learning.py appending to `$XDG_DATA_HOME/gmuse/history.jsonl` per [data-model.md § LearningRecord persistence](data-model.md#persistence-format-jsonl)
- [ ] T067 [P] [US7] Implement history loader (`load_learning_history()`) in src/gmuse/learning.py filtering by repo_id, returning last 10 per [data-model.md § LearningHistory](data-model.md#7-learninghistory)
- [ ] T068 [P] [US7] Implement few-shot formatter (`format_learning_examples()`) in src/gmuse/learning.py per [contracts/prompt-templates.md § Learning Examples Format](contracts/prompt-templates.md#learning-examples-format)
- [ ] T069 [US7] Integrate learning into CLI flow in src/gmuse/cli/main.py: check config, load history if enabled, append record after generation
- [ ] T070 [US7] Integrate learning examples into `build_context()` in src/gmuse/prompt_builder.py
- [ ] T071 [US7] Add XDG data directory path resolver for history.jsonl location

**Acceptance Verification for US7**:
1. ✅ Given `learning_enabled = true`, when user provides final message, then edit recorded to history.jsonl
2. ✅ Given historical edits exist, when `gmuse`, then last 10 examples included in prompt as few-shot
3. ✅ Given `learning_enabled = false`, when `gmuse`, then no data stored or used
4. ✅ Given multi-repo history, when generating in repo A, then only repo A's history used

**Checkpoint**: User Story 7 complete - Learning system working!

---

## Phase 10: User Story 8 - Override Model Selection (Priority: P3)

**Goal**: Per-commit model selection for cost/quality trade-offs

**Independent Test**: Run `gmuse --model gpt-4` and verify gpt-4 is used via logs

**Reference**: [spec.md § User Story 8](spec.md#user-story-8---override-model-selection-priority-p3)

### Tests for User Story 8

- [ ] T072 [P] [US8] Add integration tests to tests/integration/test_cli.py for all 3 P3 acceptance scenarios with various --model values

### Implementation for User Story 8

- [ ] T073 [US8] Verify `--model` flag properly overrides config and auto-detection in src/gmuse/cli/main.py (should already work from Phase 2)
- [ ] T074 [US8] Verify model resolution works with explicit models, config models, and auto-detection per [research.md § LLM Provider Integration](research.md#1-llm-provider-integration)
- [ ] T075 [US8] Add logging to show which model is being used (helpful for debugging)
- [ ] T076 [US8] Update CLI help text with `--model` flag description and examples

**Acceptance Verification for US8**:
1. ✅ Given staged changes, when `gmuse --model claude-3-opus`, then claude-3-opus used
2. ✅ Given config model, when `gmuse --model gpt-3.5-turbo`, then CLI flag overrides config
3. ✅ Given no model specified, when `gmuse`, then auto-detect from env vars

**Checkpoint**: User Story 8 complete - Model override working!

---

## Phase 11: User Story 9 - Adjust Commit History Depth (Priority: P3)

**Goal**: Control number of recent commits used for style context

**Independent Test**: Run `gmuse --history-depth 10` and verify 10 commits included in prompt

**Reference**: [spec.md § User Story 9](spec.md#user-story-9---adjust-commit-history-depth-priority-p3)

### Tests for User Story 9

- [ ] T077 [P] [US9] Add integration tests to tests/integration/test_cli.py for all 4 P3 acceptance scenarios with various depth values

### Implementation for User Story 9

- [ ] T078 [US9] Verify `--history-depth` flag properly overrides config in src/gmuse/cli/main.py (should already work from Phase 2)
- [ ] T079 [US9] Verify `get_commit_history()` respects depth parameter per [data-model.md § CommitHistory](data-model.md#3-commithistory)
- [ ] T080 [US9] Handle edge case: repo has fewer commits than requested depth (use all available)
- [ ] T081 [US9] Update CLI help text with `--history-depth` flag description and examples

**Acceptance Verification for US9**:
1. ✅ Given staged changes, when `gmuse --history-depth 15`, then 15 commits used
2. ✅ Given staged changes, when `gmuse --history-depth 0`, then no commit history used
3. ✅ Given config depth=8, when `gmuse`, then 8 commits used
4. ✅ Given repo with 3 commits, when `gmuse --history-depth 10`, then all 3 used

**Checkpoint**: User Story 9 complete - History depth control working!

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories, documentation, and final validation

- [ ] T082 [P] Create docs/source/user_guide/commit_messages.md comprehensive guide expanding on [quickstart.md](quickstart.md)
- [ ] T083 [P] Create docs/source/user_guide/configuration.md documenting all config.toml options per [data-model.md § UserConfig](data-model.md#5-userconfig)
- [ ] T084 [P] Update docs/source/getting_started/quickstart.md with commit message generation example from [quickstart.md](quickstart.md)
- [ ] T085 [P] Update README.md with basic usage example and link to documentation
- [ ] T086 [P] Add Google-style docstrings to all public functions in src/gmuse/*.py per [plan.md § Code Quality Gate](plan.md#code-quality-gate-)
- [ ] T087 [P] Run mypy on all new modules and fix any type errors
- [ ] T088 [P] Run Ruff on all new modules and fix any linting issues
- [ ] T089 Add performance test in tests/integration/test_performance.py verifying <10s latency for typical diffs per [spec.md § Success Criteria SC-001](spec.md#success-criteria-mandatory)
- [ ] T090 Add token usage monitoring test verifying prompts stay under 8K tokens per [plan.md § Performance Gate](plan.md#performance-gate-)
- [ ] T091 Verify all error messages match specification per [plan.md § UX Gate Error Messages](plan.md#ux-gate-)
- [ ] T092 Run full integration test suite covering all 9 user stories
- [ ] T093 Verify 85% code coverage for all new modules per [plan.md § Testing Gate](plan.md#testing-gate-)
- [ ] T094 Manual validation: Follow [quickstart.md](quickstart.md) steps end-to-end in fresh environment
- [ ] T095 Security review: Verify no API keys logged, sensitive data in learning history follows privacy guidelines per [data-model.md § Privacy & Security](data-model.md#privacy--security-considerations)
- [ ] T096 [P] Add CHANGELOG.md entry documenting new feature
- [ ] T097 [P] Update planning/roadmap.md marking v1.0 complete

**Checkpoint**: All user stories complete, tested, documented, and validated!

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phases 3-11)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed) after Phase 2
  - Or sequentially in priority order: US1 (P1) → US2-US4 (P2) → US5-US9 (P3)
- **Polish (Phase 12)**: Depends on all desired user stories being complete

### User Story Dependencies

All user stories are **independently testable** and can be implemented in any order after Phase 2 completes:

- **US1 (P1)**: Foundation only - no dependencies on other stories
- **US2 (P2)**: Foundation only - integrates with US1 but independently testable
- **US3 (P2)**: Foundation only - independently testable
- **US4 (P2)**: Foundation only - independently testable
- **US5 (P3)**: Foundation only - independently testable
- **US6 (P3)**: Foundation only - independently testable (config already built)
- **US7 (P3)**: Foundation only - independently testable
- **US8 (P3)**: Foundation only - independently testable (model selection already built)
- **US9 (P3)**: Foundation only - independently testable

### Within Each User Story

1. Tests MUST be written FIRST and FAIL before implementation (TDD)
2. Tests marked [P] can run in parallel
3. Implementation tasks follow test creation
4. Story complete and validated before moving to next priority

### Parallel Opportunities

**Setup Phase** (All can run in parallel):
- T001, T002, T003, T004, T005

**Foundational Phase** (Many can run in parallel):
- Config module: T006-T009 (sequential within config)
- Git utils module: T010-T014 (sequential within git_utils)
- LLM client module: T015-T018 (sequential within llm_client)
- Prompt builder module: T019-T023 (sequential within prompt_builder)
- T024, T025 can run anytime

**Within Each User Story**:
- All test tasks marked [P] can run in parallel
- Implementation tasks follow their module's internal sequence

**After Foundational Phase**:
- All user stories (US1-US9) can be worked on in parallel by different developers
- Recommended sequence if sequential: P1 → P2 → P3

**Polish Phase** (Many can run in parallel):
- T082-T088, T096-T097 all parallelizable
- T089-T095 depend on implementation completion

---

## Parallel Example: User Story 1 (MVP)

```bash
# After Foundational Phase completes, launch US1:

# Step 1: Write all tests in parallel
Task T026: tests/unit/test_config.py
Task T027: tests/unit/test_git_utils.py
Task T028: tests/unit/test_llm_client.py
Task T029: tests/unit/test_prompt_builder.py
(Wait for tests to be written and FAILING)

# Step 2: Integration test
Task T030: tests/integration/test_cli.py

# Step 3: CLI implementation (sequential)
Task T031: Add generate command
Task T032: Implement main flow
Task T033: Add error handling
Task T034: Add help text
Task T035: Set exit codes
Task T036: Add logging

# Step 4: Validate
Run tests → All should PASS
Verify all 5 acceptance scenarios
```

---

## Implementation Strategy

### MVP First (Recommended)

1. Complete Phase 1: Setup → ~1 day
2. Complete Phase 2: Foundational → ~5-7 days (parallel: 3-4 days)
3. Complete Phase 3: User Story 1 (MVP) → ~3-4 days
4. **STOP and VALIDATE**: Test US1 independently, demo if ready
5. Optional: Deploy MVP before continuing

### Incremental Delivery

After MVP (US1), add user stories in priority order:

1. US1 (P1) → MVP deployed ✅
2. US2-US4 (P2) → Enhanced version with hints/clipboard/formats
3. US5-US9 (P3) → Full-featured version with config/learning

Each user story adds value without breaking previous stories.

### Parallel Team Strategy

With 3-4 developers after Foundational phase:

1. Team completes Setup + Foundational together (~1 week)
2. Split into user stories:
   - Developer A: US1 (P1) - critical path
   - Developer B: US2 + US3 (P2)
   - Developer C: US4 (P2)
   - Developer D: Start US5 (P3)
3. Stories merge independently as completed

---

## Implementation Roadmap Reference

For detailed implementation guidance, see:

- **[plan.md § Implementation Roadmap](plan.md#implementation-roadmap)**: Step-by-step module implementation
- **[research.md](research.md)**: Technical decisions and rationale
- **[data-model.md](data-model.md)**: Entity definitions and validation rules
- **[contracts/prompt-templates.md](contracts/prompt-templates.md)**: Prompt structure and formats
- **[quickstart.md](quickstart.md)**: User-facing usage examples

---

## Task Statistics

- **Total Tasks**: 97
- **Phases**: 12
- **User Stories Covered**: 9 (US1-US9)
- **Parallelizable Tasks**: 47 tasks marked [P]
- **Test Tasks**: 13 (covering unit + integration)
- **MVP Tasks (Setup + Foundational + US1)**: 36 tasks
- **Estimated Timeline**:
  - MVP (US1): 2-3 weeks (1 developer) or 1-2 weeks (parallel team)
  - Full feature (US1-US9): 6-8 weeks (1 developer) or 3-4 weeks (parallel team)

---

## Notes

- All tasks follow **strict checklist format**: `- [ ] [TaskID] [P?] [Story?] Description with file path`
- **[P]** indicates parallelizable tasks (different files, no blocking dependencies)
- **[Story]** label (e.g., US1, US2) maps task to specific user story for traceability
- Each user story is **independently completable and testable**
- **Tests written FIRST** (TDD) - must fail before implementation
- Commit after each task or logical task group
- Stop at checkpoints to validate stories independently
- Constitution compliance: 85% coverage, type hints, docstrings, Ruff/mypy passing
