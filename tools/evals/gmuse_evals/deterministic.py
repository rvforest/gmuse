"""Deterministic, format-valid response policy for check mode."""

from __future__ import annotations

from typing import Literal, cast

DeterministicFormat = Literal["freeform", "conventional", "gitmoji"]


def format_valid_v1(
    format_name: DeterministicFormat,
    *,
    case_id: str = "eval",
    change_type: str = "change",
    max_chars: int | None = None,
) -> str:
    """Return a stable message accepted by gmuse's production validator.

    The policy is intentionally a check-mode plumbing signal, not a quality
    claim. It uses case identity so Inspect logs remain easy to correlate.
    """
    if change_type == "docs":
        subject = "update documentation workflow"
        conventional_type = "docs"
        emoji = "📝"
    elif "injection" in case_id or change_type == "test":
        subject = "cover untrusted fixture content"
        conventional_type = "test"
        emoji = "✅"
    else:
        subject = f"record {change_type} fixture behavior"
        conventional_type = "chore"
        emoji = "🔧"

    if format_name == "freeform":
        message = f"Update {subject} ({case_id})"
    elif format_name == "conventional":
        message = f"{conventional_type}(evals): {subject}"
    elif format_name == "gitmoji":
        message = f"{emoji} {subject} ({case_id})"
    else:
        raise ValueError(f"unsupported deterministic format: {format_name}")

    if max_chars is not None and len(message) > max_chars:
        if format_name == "conventional":
            prefix = f"{conventional_type}: "
            message = prefix + subject[: max(1, max_chars - len(prefix))]
        elif format_name == "gitmoji":
            message = f"{emoji} " + subject[: max(1, max_chars - 2)]
        else:
            message = message[:max_chars].rstrip()
    return message


def deterministic_response(
    *,
    format: str,
    case_id: str,
    change_type: str,
    max_chars: int | None = None,
    **_: object,
) -> str:
    """Response-generator callback compatible with ``generate_message_attempt``."""
    return format_valid_v1(
        cast(DeterministicFormat, format),
        case_id=case_id,
        change_type=change_type,
        max_chars=max_chars,
    )


__all__ = ["DeterministicFormat", "deterministic_response", "format_valid_v1"]
