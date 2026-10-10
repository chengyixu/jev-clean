"""Explicit pinned BASE Laya loader for reproducible learning baselines.

App LayaAdvisor now loads a trained adapter. Research must not accidentally start
from that runtime state while describing results as the original base checkpoint.
"""


def load_research_base():
    import laya_mlx

    from jev_clean.infrastructure.model import prepare_checkpoint

    return laya_mlx.load(str(prepare_checkpoint()))
