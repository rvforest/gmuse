# Research: zsh completions for gmuse

**Status**: Phase 0 Complete
**Date**: 2025-12-16

## 1. Zsh JSON Parsing

**Decision**: Use `sed` / `awk` to parse the JSON output from `gmuse completions-run`.

**Rationale**:
- The specification requires the runtime helper to return JSON.
- Zsh does not have a native JSON parser.
- We want to avoid adding `jq` as a hard dependency for users.
- The JSON structure is simple and flat (mostly), so regex-based extraction with standard tools like `sed` or `awk` is sufficient and robust enough for this specific use case.

**Implementation Details**:
```zsh
# Example extraction
local json_output='{"suggestion": "feat: add login", "status": "ok"}'
local suggestion=$(echo "$json_output" | sed -n 's/.*"suggestion": *"\([^"]*\)".*/\1/p')
```
*Note*: We need to handle escaped quotes in the JSON string carefully.

## 2. Warning Message for "No Staged Changes"

**Decision**: Use `_message` (or `_message -r`) to display the warning.

**Rationale**:
- `_message` is the standard Zsh completion function for displaying information when no completions are available or to provide context.
- It does not insert text into the command line.
- It does not mess up the prompt/buffer.

**Implementation Details**:
```zsh
_message -r "gmuse: No staged changes detected"
```

## 3. Caching & Rate Limiting

**Decision**: Implement caching and rate-limiting primarily in the **Zsh script** using `_store_cache` and `_retrieve_cache`.

**Rationale**:
- **Performance**: Checking a cache file in Zsh is much faster than spinning up the Python interpreter to check a cache.
- **Latency**: We want to minimize the delay before the suggestion appears.
- **Rate Limiting**: Can be implemented by checking the timestamp of the cache file or a separate timestamp file in Zsh before calling Python.

**Implementation Details**:
- Use `_store_cache` to save the JSON output.
- Use a custom cache policy function (`_gmuse_cache_policy`) to invalidate the cache after `GMUSE_COMPLETIONS_CACHE_TTL` (default 30s).
- For rate limiting, we can check the modification time of a "last_run" file.

## 4. Installation Method

**Decision**: Use `eval "$(gmuse completions zsh)"` in `~/.zshrc`.

**Rationale**:
- Simpler installation: single line added to `.zshrc`.
- No need to manage file paths or create directories.
- Script is always up-to-date with the installed version of gmuse.
- Common pattern used by many CLI tools (e.g., `pyenv`, `rbenv`, `starship`).

**Implementation Details**:
- The `gmuse completions zsh` command prints the completion script to stdout.
- Users add `eval "$(gmuse completions zsh)"` to their `.zshrc`.
- Zsh-side caching still uses `$XDG_CACHE_HOME` for cache files.
