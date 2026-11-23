"""Suite-composition collection and goal evaluation."""

from __future__ import annotations

from collections.abc import Sequence

from gmuse.config import DEFAULTS

from .models import (
    INJECTION_LOCATION_TAGS,
    INJECTION_PATTERN_TAGS,
    CompositionEntry,
    CompositionGoalResult,
    CompositionGroup,
    EvalCase,
    EvalSuite,
    SuiteComposition,
    ValidationIssue,
)
from .results import ResolvedCase

_CHANGE_LABELS = {
    "feat": "Features",
    "fix": "Fixes",
    "docs": "Documentation",
    "style": "Style",
    "refactor": "Refactoring",
    "test": "Tests",
    "chore": "Chores",
}
_FORMAT_LABELS = {
    "freeform": "Freeform",
    "conventional": "Conventional",
    "gitmoji": "Gitmoji",
}
_CONTEXT_LABELS = {
    "history": "Commit history",
    "branch": "Branch context",
    "hint": "User hint",
    "max_chars": "Maximum length",
}
_GROUP_ORDER = (
    "Changes",
    "Output formats",
    "Context variations",
    "Safety scenarios",
    "Fixture sources",
)
_CONTEXT_ORDER = ("history", "branch", "hint", "max_chars")
_FORMAT_ORDER = ("freeform", "conventional", "gitmoji")


def resolved_history_depth(case: EvalCase) -> int:
    """Resolve an omitted case depth using gmuse's current default.

    Example:
        >>> resolved_history_depth(case) >= 0
        True
    """
    configured = (
        DEFAULTS["history_depth"] if case.history_depth is None else case.history_depth
    )
    return int(configured)


def _human_injection_scenario(tags: set[str]) -> str:
    pattern_labels = {
        "direct": "Direct instruction",
        "direct-instruction": "Direct instruction",
        "indirect": "Indirect instruction",
        "indirect-external-content": "Indirect external content",
        "obfuscated": "Obfuscated instruction",
        "obfuscated-encoded": "Obfuscated instruction",
        "encoded": "Encoded instruction",
        "deleted": "Deleted instruction",
        "deleted-instruction": "Deleted instruction",
    }
    location_labels = {
        "code-comment": "code comment",
        "markdown": "Markdown",
        "docs": "documentation",
        "string-literal": "string literal",
        "test-fixture": "test fixture",
        "config-example": "configuration example",
    }
    patterns = sorted(tags.intersection(pattern_labels))
    locations = sorted(tags.intersection(location_labels))
    if patterns and locations:
        return f"{pattern_labels[patterns[0]]} in {location_labels[locations[0]]}"
    if patterns:
        return pattern_labels[patterns[0]]
    return "Injection scenario"


def _entry_sort_key(group_name: str, key: str) -> tuple[int, int | str]:
    """Return an explicit, stable ordering key for one composition entry."""
    category = key.split(":")[1]
    if group_name == "Context variations":
        return (0, _CONTEXT_ORDER.index(category))
    if group_name == "Output formats":
        return (0, _FORMAT_ORDER.index(category))
    if group_name == "Safety scenarios":
        return (0 if key == "safety:ordinary" else 1, key)
    return (0, key)


def collect_suite_composition(cases: Sequence[ResolvedCase]) -> SuiteComposition:
    """Collect stable, human-readable case counts for a suite.

    Each case contributes once to every applicable entry. Multi-format cases
    therefore contribute to multiple format entries without inflating any one
    entry.

    Example:
        >>> collect_suite_composition([]).groups
        []
    """
    values: dict[str, dict[str, tuple[str, int]]] = {
        group: {} for group in _GROUP_ORDER
    }

    def add(group: str, key: str, label: str) -> None:
        previous = values[group].get(key)
        count = previous[1] if previous else 0
        values[group][key] = (label, count + 1)

    for item in cases:
        fixture = item.fixture
        case = item.case
        change_label = _CHANGE_LABELS.get(
            fixture.change_type, fixture.change_type.replace("_", " ").title()
        )
        add("Changes", f"change:{fixture.change_type}", change_label)

        for format_name in case.formats:
            add(
                "Output formats",
                f"format:{format_name}",
                _FORMAT_LABELS[format_name],
            )

        context_values = {
            "history": bool(resolved_history_depth(case)),
            "branch": case.include_branch,
            "hint": bool(case.user_hint),
            "max_chars": case.max_chars is not None,
        }
        for context_name in _CONTEXT_ORDER:
            state = "enabled" if context_values[context_name] else "disabled"
            add(
                "Context variations",
                f"context:{context_name}:{state}",
                f"{_CONTEXT_LABELS[context_name]} {state}",
            )

        is_injection = "injection" in fixture.safety_tags or bool(
            fixture.injection_tags
        )
        if is_injection:
            scenario = _human_injection_scenario(set(fixture.injection_tags))
            add("Safety scenarios", f"safety:injection:{scenario}", scenario)
        else:
            add("Safety scenarios", "safety:ordinary", "Ordinary change")

        origin_label = {
            "real": "Real",
            "adapted": "Adapted",
            "synthetic": "Synthetic",
        }[fixture.origin]
        add("Fixture sources", f"source:{fixture.origin}", origin_label)

    groups: list[CompositionGroup] = []
    for group_name in _GROUP_ORDER:
        entries = values[group_name]
        if not entries:
            continue
        ordered = sorted(
            entries.items(), key=lambda pair: _entry_sort_key(group_name, pair[0])
        )
        groups.append(
            CompositionGroup(
                name=group_name,
                entries=[
                    CompositionEntry(key=key, label=label, case_count=count)
                    for key, (label, count) in ordered
                ],
            )
        )
    return SuiteComposition(groups=groups)


def _goal_values(item: ResolvedCase, selector: str) -> set[str]:
    fixture = item.fixture
    case = item.case
    if selector == "fixture.origin":
        return {fixture.origin}
    if selector == "fixture.ecosystem":
        return {fixture.ecosystem}
    if selector == "fixture.change_type":
        return {fixture.change_type}
    if selector == "fixture.source_repository":
        return {fixture.provenance.source_owner_repo or "synthetic"}
    if selector == "case.format":
        return set(case.formats)
    if selector == "context.history":
        return {"enabled" if resolved_history_depth(case) else "disabled"}
    if selector == "context.branch":
        return {"enabled" if case.include_branch else "disabled"}
    if selector == "context.hint":
        return {"enabled" if case.user_hint else "disabled"}
    if selector == "context.max_chars":
        return {"enabled" if case.max_chars is not None else "disabled"}

    is_injection = "injection" in fixture.safety_tags or bool(fixture.injection_tags)
    if selector == "safety.scenario":
        return {"injection" if is_injection else "ordinary"}
    if selector == "safety.tag":
        return set(fixture.safety_tags)
    if selector == "safety.injection_pattern":
        return set(fixture.injection_tags).intersection(INJECTION_PATTERN_TAGS)
    if selector == "safety.injection_location":
        return set(fixture.injection_tags).intersection(INJECTION_LOCATION_TAGS)
    raise AssertionError(f"unhandled composition selector: {selector}")


def validate_composition_goals(
    suite: EvalSuite,
    cases: Sequence[ResolvedCase],
    *,
    strict: bool,
) -> tuple[list[CompositionGoalResult], list[ValidationIssue], list[ValidationIssue]]:
    """Evaluate required and advisory value-specific composition goals.

    Example:
        >>> results, errors, warnings = validate_composition_goals(
        ...     suite, [], strict=False
        ... )
    """
    results: list[CompositionGoalResult] = []
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    for goal in suite.composition_goals:
        observed = sum(
            goal.value in _goal_values(item, goal.selector) for item in cases
        )
        met = observed >= goal.minimum_cases
        results.append(
            CompositionGoalResult(
                selector=goal.selector,
                value=goal.value,
                observed_cases=observed,
                minimum_cases=goal.minimum_cases,
                severity=goal.severity,
                status="met" if met else "shortfall",
            )
        )
        if met:
            continue
        issue = ValidationIssue(
            code="composition_goal_shortfall",
            asset_id=suite.id,
            message=(
                f"composition goal {goal.selector}={goal.value} has {observed} cases; "
                f"requires {goal.minimum_cases} ({goal.severity})"
            ),
        )
        if goal.severity == "required" or strict:
            errors.append(issue)
        else:
            warnings.append(issue)
    return results, errors, warnings
