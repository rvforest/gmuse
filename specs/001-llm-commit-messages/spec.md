# Feature Specification: LLM-Powered Commit Message Generator

**Feature Branch**: `001-llm-commit-messages`
**Created**: November 28, 2025
**Status**: Draft
**Input**: User description: "Provide a safe, useful, and extensible CLI tool that generates commit messages using LLMs. The goal is to reduce friction in writing clear commit messages."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Basic Commit Message (Priority: P1)

A developer has made code changes and staged them with `git add`. They want a contextual commit message generated automatically without manual prompting or configuration.

**Why this priority**: This is the core value proposition - reducing friction in writing commit messages. Without this, there is no MVP.

**Independent Test**: Can be fully tested by staging changes in a git repository, running `gmuse`, and verifying a commit message is output to STDOUT. Delivers immediate value by saving time on every commit.

**Acceptance Scenarios**:

1. **Given** a git repository with staged changes, **When** the user runs `gmuse`, **Then** a commit message is generated and printed to STDOUT
2. **Given** a git repository with no staged changes, **When** the user runs `gmuse`, **Then** an error message "No staged changes found. Stage changes with `git add` or run `gmuse split` to plan commits from unstaged changes." is displayed
3. **Given** a directory that is not a git repository, **When** the user runs `gmuse`, **Then** an error message "Not a git repository — run this inside a repository folder." is displayed
4. **Given** no LLM provider API key is configured, **When** the user runs `gmuse`, **Then** an error message "No API key configured. Set `OPENAI_API_KEY` or configure provider in config.toml." is displayed
5. **Given** staged changes and a valid API key, **When** the user runs `gmuse`, **Then** the generated message reflects the content and nature of the staged diff

---

### User Story 2 - Influence Message with Runtime Hints (Priority: P2)

A developer wants to provide additional context for a specific commit without modifying persistent configuration files.

**Why this priority**: Enables per-commit customization, which is important for maintaining flexibility, but the tool is still useful without it.

**Independent Test**: Can be fully tested by running `gmuse --hint "focus on security implications"` with staged changes and verifying the generated message incorporates the hint. Delivers value by allowing commit-specific guidance.

**Acceptance Scenarios**:

1. **Given** staged changes, **When** the user runs `gmuse --hint "emphasize performance improvements"`, **Then** the generated message prominently mentions performance aspects
2. **Given** staged changes, **When** the user runs `gmuse --hint "breaking change"`, **Then** the generated message includes breaking change indicators
3. **Given** staged changes, **When** the user runs `gmuse` without a hint, **Then** the message is generated based on diff and history context only

---

### User Story 3 - Copy Message to Clipboard (Priority: P2)

A developer wants the generated message automatically copied to their clipboard for pasting into a commit dialog or editor.

**Why this priority**: Improves workflow efficiency but is not essential for core functionality. Users can manually copy from terminal output.

**Independent Test**: Can be fully tested by running `gmuse --copy` and verifying the system clipboard contains the generated message. Delivers value by eliminating manual copy-paste steps.

**Acceptance Scenarios**:

1. **Given** staged changes and clipboard functionality available, **When** the user runs `gmuse --copy`, **Then** the generated message is copied to the system clipboard and also printed to STDOUT
2. **Given** clipboard functionality unavailable, **When** the user runs `gmuse --copy`, **Then** the message is printed to STDOUT with a warning that clipboard copy failed
3. **Given** `copy_to_clipboard = true` in config.toml, **When** the user runs `gmuse` without flags, **Then** the message is automatically copied to clipboard

---

### User Story 4 - Customize Message Format Style (Priority: P2)

A developer or team wants commit messages to follow a specific convention (e.g., Conventional Commits, Gitmoji) consistently across all commits.

**Why this priority**: Supports team standards and tooling that depends on commit message format, but the tool provides value with freeform messages.

**Independent Test**: Can be fully tested by running `gmuse --format conventional` and verifying the output follows Conventional Commits format (e.g., "feat: add user authentication"). Delivers value by ensuring consistency with team conventions.

**Acceptance Scenarios**:

1. **Given** staged changes, **When** the user runs `gmuse --format conventional`, **Then** the message follows Conventional Commits format with type prefix (feat, fix, docs, etc.)
2. **Given** staged changes, **When** the user runs `gmuse --format gitmoji`, **Then** the message includes relevant emoji prefixes
3. **Given** staged changes, **When** the user runs `gmuse --format freeform`, **Then** the message is generated without enforced formatting constraints
4. **Given** `format = "conventional"` in config.toml, **When** the user runs `gmuse` without format flag, **Then** conventional format is used by default

---

### User Story 5 - Repository-Level Instructions (Priority: P3)

A repository maintainer wants to provide project-specific guidance for commit message generation that applies to all contributors without individual configuration.

**Why this priority**: Enables project-level customization and consistency but can be achieved with hints or config for individual users initially.

**Independent Test**: Can be fully tested by creating a `.gmuse` file at repository root with instructions like "Always mention ticket numbers", running `gmuse`, and verifying the instruction is reflected in the output. Delivers value by standardizing commit practices across teams.

**Acceptance Scenarios**:

1. **Given** a `.gmuse` file at repository root with content "Always reference issue numbers", **When** the user runs `gmuse`, **Then** the generated message attempts to identify and reference relevant issue numbers
2. **Given** both `.gmuse` file and `--hint` argument, **When** the user runs `gmuse`, **Then** both instructions influence the message with CLI hint taking precedence for conflicts
3. **Given** no `.gmuse` file exists, **When** the user runs `gmuse`, **Then** the message is generated without repository-specific instructions

---

### User Story 6 - Global Configuration (Priority: P3)

A developer wants to set personal preferences (default model, clipboard behavior, message format) that persist across all their projects without per-repository setup.

**Why this priority**: Improves user experience for frequent users but not required for basic functionality. CLI flags can substitute for most config options.

**Independent Test**: Can be fully tested by creating `$XDG_CONFIG_HOME/gmuse/config.toml` with `copy_to_clipboard = true`, running `gmuse`, and verifying clipboard behavior matches config. Delivers value by reducing repetitive flag usage.

**Acceptance Scenarios**:

1. **Given** config.toml with `copy_to_clipboard = true`, **When** the user runs `gmuse`, **Then** the message is automatically copied to clipboard
2. **Given** config.toml with `model = "gpt-4"`, **When** the user runs `gmuse`, **Then** the gpt-4 model is used for generation
3. **Given** config.toml with `history_depth = 10`, **When** the user runs `gmuse`, **Then** 10 recent commits are used for style context
4. **Given** no config.toml exists, **When** the user runs `gmuse`, **Then** reasonable defaults are used (no clipboard copy, auto-detected model, 5 commit history)

---

### User Story 7 - Override Model Selection (Priority: P3)

A developer wants to use a specific LLM model for a particular commit (e.g., a more powerful model for complex changes, or a cheaper model for simple formatting fixes).

**Why this priority**: Provides flexibility for cost/quality trade-offs but not essential for basic usage. Default model selection works for most cases.

**Independent Test**: Can be fully tested by running `gmuse --model gpt-4` and verifying that the gpt-4 model is used (via logs or provider API call inspection). Delivers value by optimizing cost and quality on a per-commit basis.

**Acceptance Scenarios**:

1. **Given** staged changes, **When** the user runs `gmuse --model claude-3-opus`, **Then** the claude-3-opus model is used for generation
2. **Given** a configured default model in config.toml, **When** the user runs `gmuse --model gpt-3.5-turbo`, **Then** the CLI flag overrides the config default
3. **Given** no model specified and no config, **When** the user runs `gmuse`, **Then** a model is auto-detected based on available environment variables (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)

---

### User Story 8 - Adjust Commit History Depth (Priority: P3)

A developer wants to control how many recent commits are used as style context, either to provide more examples for better pattern matching or fewer for faster generation.

**Why this priority**: Fine-tuning parameter that improves results in specific scenarios but is not critical for core functionality. Default of 5 commits is reasonable for most use cases.

**Independent Test**: Can be fully tested by running `gmuse --history-depth 10` and verifying 10 commit messages are included in the prompt context. Delivers value by allowing users to optimize generation quality versus speed.

**Acceptance Scenarios**:

1. **Given** staged changes, **When** the user runs `gmuse --history-depth 15`, **Then** 15 recent commit messages are used as style context
2. **Given** staged changes, **When** the user runs `gmuse --history-depth 0`, **Then** no commit history is used (only diff and instructions)
3. **Given** `history_depth = 8` in config.toml, **When** the user runs `gmuse` without the flag, **Then** 8 commits are used as context
4. **Given** a repository with only 3 commits, **When** the user runs `gmuse --history-depth 10`, **Then** all 3 available commits are used

---

### Edge Cases

- **Large diffs**: When staged changes exceed reasonable token limits, the tool should either truncate intelligently (keeping function signatures, removing repeated patterns) or warn the user to split the commit.
- **No commit history**: When generating a message for the first commit in a repository, the tool should gracefully handle the absence of commit history context.
- **Network failures**: If the LLM API is unreachable or times out, the tool should display an actionable error message with retry suggestions.
- **Invalid configuration**: If config.toml contains invalid TOML syntax or unrecognized keys, the tool should display a clear error pointing to the problematic line/key.
- **Clipboard unavailable**: On systems without clipboard support (e.g., headless servers), the `--copy` flag should degrade gracefully with a warning rather than failing.
- **Binary or non-text diffs**: When staged changes include binary files, the diff may not be meaningful text. The tool should acknowledge this and either exclude binary content from the prompt or mention the file type in the message.
- **Empty commits**: When attempting to generate a message for an empty commit (allowed with `--allow-empty`), the tool should prompt for a hint or generate a generic message.

## Constitution Check (Mandatory)

- **Code Quality**: This spec introduces a new CLI command structure and public API for message generation. All public functions will have type hints (mypy enforcement), Google-style docstrings, and will follow existing project patterns. New modules include prompt building, LLM client abstraction, and config parsing. All changes will be linted with Ruff and type-checked with mypy before merge.

- **Testing**: Unit tests will be added for each module:
  - `tests/unit/test_config.py` - config parsing and validation
  - `tests/unit/test_prompt_builder.py` - prompt assembly logic
  - `tests/unit/test_llm_client.py` - LLM client abstraction (mocked API calls)
  - `tests/unit/test_git_utils.py` - git operations (diff extraction, history retrieval)
  - `tests/integration/test_cli.py` - end-to-end CLI scenarios with mocked LLM responses

  Coverage target: 85% for all new modules. Integration tests will cover all user stories in priority order (P1 first).

- **UX**: CLI help text, error messages, and user documentation will be added for:
  - `gmuse --help` output with all flags and examples
  - Error messages for all failure scenarios (no repo, no staged changes, no API key, network failures, invalid config)
  - User guide documentation in `docs/source/user_guide/commit_messages.md`
  - Quickstart guide updates in `docs/source/getting_started/quickstart.md`
  - Configuration reference in `docs/source/user_guide/configuration.md`

- **Performance**:
  - Generation latency: Target under 10 seconds for typical diffs (< 1000 lines) using standard models (GPT-3.5/4, Claude)
  - Token consumption: Implement intelligent diff truncation to keep prompts under 8K tokens for compatibility with most models
  - Network timeout: Set reasonable timeouts (30 seconds default) with clear error messages when exceeded
  - Config loading: Config files parsed once at startup with caching for repeat invocations

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST validate that the current working directory is inside a git repository before attempting message generation
- **FR-002**: System MUST validate that staged changes exist before generating a message
- **FR-003**: System MUST extract staged diff using `git diff --cached`
- **FR-004**: System MUST collect recent commit messages (default 5) to provide style context unless history depth is set to 0
- **FR-005**: System MUST build a prompt combining system instructions, optional repository-level instructions from `.gmuse` file, optional user-level instructions, commit history, optional runtime hint, and staged diff
- **FR-006**: System MUST support LLM provider auto-detection based on environment variables (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
- **FR-007**: System MUST call the selected LLM provider and return the generated message to STDOUT
- **FR-008**: System MUST support `--hint` flag to provide per-run contextual guidance
- **FR-009**: System MUST support `--copy` flag to copy generated message to system clipboard
- **FR-010**: System MUST support `--model` flag to override default model selection
- **FR-011**: System MUST support `--format` flag with values "freeform" (default), "conventional", and "gitmoji"
- **FR-012**: System MUST support `--history-depth` flag to control number of recent commits used as context
- **FR-013**: System MUST read global configuration from `$XDG_CONFIG_HOME/gmuse/config.toml` if it exists
- **FR-014**: System MUST support config keys: `model`, `copy_to_clipboard`, `history_depth`, `format`
- **FR-015**: System MUST read repository-level instructions from `.gmuse` file at repository root if it exists
- **FR-016**: System MUST prioritize configuration in order: CLI flags > config.toml > defaults
- **FR-017**: System MUST provide clear, actionable error messages for: not a git repo, no staged changes, no API key, network failures, invalid config
- **FR-018**: System MUST handle network timeouts gracefully with appropriate error messages
- **FR-019**: System MUST truncate large diffs intelligently to stay within token limits while preserving meaningful context
- **FR-020**: System MUST handle repositories with no commit history (first commit) without errors
- **FR-021**: System MUST handle clipboard unavailability gracefully, displaying warning instead of failing
- **FR-022**: System MUST handle binary files in staged changes appropriately

### Key Entities

- **CommitMessage**: The generated text output representing a commit message; attributes include content string, format style, timestamp of generation
- **StagedDiff**: The git diff output for staged changes; attributes include raw diff text, file paths changed, number of lines added/removed
- **CommitHistory**: Collection of recent commit messages used for style context; attributes include commit hash, message text, author, timestamp, limited to configurable depth
- **RepositoryInstructions**: Text from `.gmuse` file at repository root; represents project-level guidance for commit message generation
- **UserConfig**: Configuration loaded from `$XDG_CONFIG_HOME/gmuse/config.toml`; attributes include model preference, clipboard behavior, history depth, message format

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can generate a commit message for staged changes in under 10 seconds for typical diffs (< 1000 lines)
- **SC-002**: 90% of generated messages require minimal or no editing before use (measured subjectively via user feedback after v1 release)
- **SC-003**: System handles all specified error conditions (no repo, no staged changes, no API key, network failures) with actionable error messages that allow users to resolve issues independently
- **SC-004**: Users can customize message generation behavior via configuration without editing code (verified by testing all config options)
- **SC-005**: Generated messages reflect the style of recent commit history when 5+ commits exist in the repository (verified by comparing message format to commit history patterns)
- **SC-006**: Zero-config first-time setup works for users with standard environment variables (OPENAI_API_KEY or equivalent) - no manual configuration required for basic usage
- **SC-007**: CLI help text and error messages enable users to resolve 95% of issues without consulting external documentation (measured via support request frequency)
- **SC-008**: Message format options (freeform, conventional, gitmoji) produce correctly formatted output that passes format validation tools (e.g., commitlint for conventional commits)
- **SC-009**: Repository-level instructions in `.gmuse` file demonstrably influence message content across multiple test cases (verified by A/B testing with and without instructions)
