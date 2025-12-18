#!/usr/bin/env zsh
#compdef git

# gmuse zsh completion script
# Provides AI-generated commit message suggestions for 'git commit -m'
#
#
# Installation:
#   Add to your ~/.zshrc:
#     eval "$(gmuse completions zsh)"
#
#   Then restart your shell:
#     exec zsh
#
# The runtime helper can be invoked in multiple ways; the completion will
# try `gmuse completions-run` first and fall back to `python3 -m gmuse.cli.main`.
# This helps environments where the CLI is available as a module but not
# installed as an executable. The script will also check for `command -v gmuse`.

# UX note: To avoid surprising behavior, this completion only generates an AI
# suggestion when the `-m/--message` argument is empty (i.e., `git commit -m ` + TAB).

# Cache policy for gmuse completions
_gmuse_cache_policy() {
    local cache_ttl="${GMUSE_COMPLETIONS_CACHE_TTL:-30}"
    local -a oldp
    # Invalidate cache if older than cache_ttl seconds
    oldp=( "$1"(Nms+${cache_ttl}) )
    (( $#oldp ))
}

# Helper to invoke runtime helper with fallbacks
_gmuse_invoke_helper() {
    if command -v gmuse >/dev/null 2>&1; then
        gmuse completions-run --shell zsh --for "git commit -m" --timeout "$1" 2>/dev/null
    else
        # Try running the module directly as a fallback
        python3 -m gmuse.cli.main completions-run --shell zsh --for "git commit -m" --timeout "$1" 2>/dev/null || true
    fi
}

# Main completion function for git commit -m
_gmuse_git_commit_message() {
    # Check if completions are enabled
    if [[ "${GMUSE_COMPLETIONS_ENABLED:-true}" != "true" ]]; then
        return 1
    fi

    local curcontext="$curcontext" state
    local -a suggestions
    local hint="${words[CURRENT]}"
    local timeout="${GMUSE_COMPLETIONS_TIMEOUT:-3.0}"
    local cache_key="gmuse_commit_suggestion"
    local json_output suggestion gmuse_status

    # Avoid surprising behavior: only generate a suggestion when the message
    # argument is empty (i.e., user typed `git commit -m ` then TAB).
    if [[ -n "$hint" ]]; then
        return 1
    fi

    # Try to retrieve from cache first
    if _cache_invalid "$cache_key" || ! _retrieve_cache "$cache_key"; then
        # Call the runtime helper (with fallbacks)
        json_output=$(_gmuse_invoke_helper "$timeout")

        if [[ -z "$json_output" ]]; then
            _message -r "gmuse: Failed to generate suggestion"
            return 1
        fi

        # Parse JSON output using sed (avoiding jq dependency)
        gmuse_status=$(echo "$json_output" | sed -n 's/.*"status"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
        suggestion=$(echo "$json_output" | sed -n 's/.*"suggestion"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')

        # Handle non-ok statuses
        case "$gmuse_status" in
            no_staged_changes)
                _message -r "gmuse: No staged changes detected"
                return 1
                ;;
            timeout)
                _message -r "gmuse: Request timed out"
                return 1
                ;;
            offline)
                _message -r "gmuse: Offline or credentials missing"
                return 1
                ;;
            error)
                _message -r "gmuse: Error generating suggestion"
                return 1
                ;;
            ok)
                if [[ -n "$suggestion" ]]; then
                    suggestions=("$suggestion")
                    _store_cache "$cache_key" suggestions
                fi
                ;;
        esac
    fi

    # Provide the suggestion as a completion
    if [[ -n "${suggestions[1]}" ]]; then
        compadd -S '' -- "${suggestions[@]}"
        return 0
    fi

    return 1
}

# Hook into git completion for commit -m
_git_commit_message_gmuse() {
    # Only activate for git commit -m pattern
    if [[ "${words[1]}" == "git" && "${words[2]}" == "commit" ]]; then
        local i
        for ((i = 3; i <= CURRENT; i++)); do
            if [[ "${words[i]}" == "-m" || "${words[i]}" == "--message" ]]; then
                if [[ $CURRENT -eq $((i + 1)) ]]; then
                    _gmuse_git_commit_message
                    return
                fi
            fi
        done
    fi

    # Fall back to default git completion
    _git "$@"
}

# Register with completion system using zstyle cache policy
zstyle ':completion:*' cache-path "${XDG_CACHE_HOME:-$HOME/.cache}/zsh"
zstyle ":completion:*:*:git:*" use-cache on
zstyle ":completion:*:*:git:*" cache-policy _gmuse_cache_policy

compdef _git_commit_message_gmuse git
