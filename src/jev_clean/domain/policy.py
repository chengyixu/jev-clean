"""Model judgment and execution readiness, not a filesystem cleanup classifier.

The legacy module name is retained for the wire/API callers. There are no
path, extension, age, open-handle or hard-link classification vetoes here.
"""

from dataclasses import replace

from jev_clean.domain.models import Candidate, Decision


def apply_policy(item: Candidate, decision: Decision | None = None) -> Candidate:
    """Preserve the model's judgment separately from supported staging mechanics."""
    execution_issue = item.execution_issue
    if not item.regular or item.symlink:
        execution_issue = "Executor supports regular non-symlink files only"
    elif not item.scan_complete:
        execution_issue = "Exact target metadata unavailable"
    eligible = not execution_issue
    # This validates the typed answer, not a confidence threshold or classification rule.
    recommended = bool(
        decision
        and decision.choice == "remove"
        and decision.probabilities.get("remove", 0) > 0
        and decision.probabilities.get("remove", 0) >= max(decision.probabilities.values(), default=1)
    )
    reason = f"Model chose {decision.choice}" if decision else "Awaiting mandatory model judgment"
    if execution_issue:
        reason += "; " + execution_issue
    return replace(
        item,
        eligible=eligible,
        reason=reason,
        decision=decision,
        recommended=recommended,
        execution_issue=execution_issue,
    )
