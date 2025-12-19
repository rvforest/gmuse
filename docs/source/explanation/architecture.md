# Architecture

gmuse is designed as a modular application with clear separation of concerns.

## Core Components

- **CLI**: Handles user interaction and command parsing (using Typer).
- **Git**: Interacts with the git repository to retrieve staged changes.
- **LLM**: Abstraction layer for interacting with various LLM providers (using LiteLLM).
- **Config**: Manages configuration from files and environment variables.

## Data Flow

1. User invokes `gmuse msg`.
2. **Git** module retrieves staged diffs.
3. **Config** module resolves settings.
4. **LLM** module constructs a prompt with the diff and sends it to the provider.
5. **LLM** provider returns a commit message.
6. **CLI** displays or copies the message.
