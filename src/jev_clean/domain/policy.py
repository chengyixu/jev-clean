"""Learned Laya judgment plus execution-readiness checks.

No folder/tag classification admission gates. Model approval never bypasses human
confirmation, native operation contracts, identity or descendant manifest checks.
"""

from collections.abc import Sequence
from dataclasses import replace
from pathlib import PurePath

from jev_clean.domain.models import Candidate, Decision

OWNER_STORE_ISSUE = "owner-managed store: only the owner-native operation is supported"


def apply_policy(
    item: Candidate, decision: Decision | None = None, owner_stores: Sequence[PurePath] = ()
) -> Candidate:
    """Preserve learned judgment separately from execution readiness.

    owner_stores are the verified stores of installed package managers. Moving one of them,
    a part of one, or a directory holding one to Trash bypasses its owner; only the owner's
    native operation is executable there, whatever the model chose.
    """
    execution_issue = item.execution_issue
    path = PurePath(item.path)
    if item.symlink or (not item.regular and item.unit != "directory"):
        execution_issue = "Executor supports regular files and non-symlink directory resources only"
    elif not item.scan_complete:
        execution_issue = "Exact target metadata unavailable"
    elif item.operation == "trash" and any(
        path.is_relative_to(store) or store.is_relative_to(path) for store in owner_stores
    ):
        execution_issue = OWNER_STORE_ISSUE
    eligible = not execution_issue
    # This validates the typed answer, not a confidence threshold or classification rule.
    recommended = bool(
        decision
        and decision.choice == "remove"
        and decision.probabilities.get("remove", 0) > 0
        and decision.probabilities.get("remove", 0) >= max(decision.probabilities.values(), default=1)
    )
    reason = f"Model chose {decision.choice}" if decision else "Awaiting mandatory model judgment"
    if decision and decision.agreement:
        reason += f" ({decision.agreement} answer orders agree)"
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
