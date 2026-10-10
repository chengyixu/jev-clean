"""Each supported owner operation executes only its freshly discovered native argv."""

from dataclasses import replace
from subprocess import CompletedProcess

import pytest
from test_model_owned_judgment import answer

from jev_clean.domain.policy import apply_policy
from jev_clean.infrastructure import owner_execution, owner_tools
from jev_clean.infrastructure.scanner import candidate_from_stat


@pytest.mark.parametrize(
    "owner,action",
    [
        ("go", ["clean", "-cache"]),
        ("pip", ["cache", "purge"]),
        ("npm", ["cache", "verify"]),
    ],
)
def test_supported_native_action_uses_fixed_interface_not_plan_evidence(tmp_path, monkeypatch, owner, action):
    root = tmp_path / "store"
    root.mkdir()
    item = apply_policy(
        replace(
            candidate_from_stat(root, root.stat(), tmp_path, set()),
            unit="directory",
            operation="owner_prune",
            owner_tool=owner,
            execution_issue="",
            action_evidence="Untrusted saved text: rm -rf personal",
        ),
        answer("remove"),
    )
    observation = {
        "owner": owner,
        "path": str(root),
        "argv": ["/installed/" + owner, *action],
        "active": False,
    }
    monkeypatch.setattr(owner_tools, "owner_observations", lambda: [observation])
    calls = []

    def runner(argv, **kwargs):
        calls.append(argv)
        assert kwargs["env"]["COREPACK_ENABLE_NETWORK"] == "0"
        assert kwargs["timeout"] == 120
        return CompletedProcess(argv, 0, stdout="owner receipt", stderr="")

    receipt = owner_execution.prune_selected(item, runner=runner)
    assert calls == [["/installed/" + owner, *action]]
    assert receipt["complete"] and not receipt["reversible"]
    assert root.exists()


def test_owner_target_rediscovery_does_not_execute_old_location(tmp_path, monkeypatch):
    root = tmp_path / "old"
    root.mkdir()
    item = replace(
        candidate_from_stat(root, root.stat(), tmp_path, set()),
        unit="directory",
        operation="owner_prune",
        owner_tool="go",
    )
    monkeypatch.setattr(
        owner_tools,
        "owner_observations",
        lambda: [
            {
                "owner": "go",
                "path": str(tmp_path / "new"),
                "argv": ["/go", "clean", "-cache"],
                "active": False,
            }
        ],
    )
    with pytest.raises(ValueError, match="contract changed"):
        owner_execution.prune_selected(item, runner=lambda *a, **kw: pytest.fail("must not execute"))
    assert root.exists()
