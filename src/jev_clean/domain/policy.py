"""Model judgment is not permission: independent disposal evidence is required.

Preserve raw model answers; unverified personal/mixed resources cannot become
selectable from remove alone. No folder-name blacklist or confidence threshold.
"""

from dataclasses import replace

from jev_clean.domain.models import Candidate, Decision


def apply_policy(item: Candidate, decision: Decision | None = None) -> Candidate:
    """Preserve raw judgment separately from evidence-backed cleanup authorization."""
    execution_issue = item.execution_issue
    if item.symlink or (not item.regular and item.unit != "directory"):
        execution_issue = "Executor supports regular files and non-symlink directory resources only"
    elif not item.scan_complete:
        execution_issue = "Exact target metadata unavailable"
    if not execution_issue and not (item.disposal and item.disposal.covers(item.path)):
        execution_issue = "No independently observed disposal evidence"
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
