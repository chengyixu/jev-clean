"""Shared wire contract for both human and agent clients."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Fingerprint:
    device: int
    inode: int
    size: int
    mtime_ns: int
    ctime_ns: int
    uid: int
    nlink: int


@dataclass(frozen=True)
class Decision:
    choice: str
    probabilities: dict[str, float]
    backend: str
    elapsed_ms: float
    reused: bool = False


@dataclass(frozen=True)
class Candidate:
    id: str
    path: str
    kind: str
    allocated_bytes: int
    age_seconds: float
    fingerprint: Fingerprint
    regular: bool
    symlink: bool
    scan_complete: bool
    open_file: bool | None = None
    eligible: bool = False
    reason: str = "Not evaluated"
    decision: Decision | None = None
    recommended: bool = False
    context_hint: str = ""

    @property
    def selectable(self) -> bool:
        return self.eligible and self.recommended and self.decision is not None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Candidate:
        value = dict(data)
        value.pop("selectable", None)  # Derived, never trusted from a saved plan.
        value["fingerprint"] = Fingerprint(**value["fingerprint"])
        value["decision"] = Decision(**value["decision"]) if value.get("decision") else None
        return cls(**value)


@dataclass
class ScanReport:
    candidates: list[Candidate] = field(default_factory=list)
    complete: bool = True
    warnings: list[str] = field(default_factory=list)
    files_seen: int = 0
    elapsed_ms: float = 0


@dataclass(frozen=True)
class CategoryReport:
    timestamp: str
    used_bytes: int
    system_bytes: int
    named: dict[str, int]
    other_bytes: int
    source: str = "macOS StorageManagementService (private, version-dependent log)"

    @property
    def residual_bytes(self) -> int:
        return self.used_bytes - self.system_bytes - sum(self.named.values())

    @property
    def discrepancy_bytes(self) -> int:
        return self.other_bytes - self.residual_bytes


@dataclass
class Measurement:
    path: str
    allocated_bytes: int | None
    complete: bool
    note: str
    category_membership: str = "unattributed"


@dataclass
class AuditReport:
    schema_version: int
    created_at: str
    home: str
    mode: str
    scan: ScanReport
    measurements: list[Measurement] = field(default_factory=list)
    categories: CategoryReport | None = None
    diagnostics: dict[str, Any] = field(default_factory=dict)
    model_status: str = "model required; not yet assessed"
    demo: bool = False
    exploration: dict[str, Any] = field(default_factory=dict)
    coverage: dict[str, Any] = field(default_factory=dict)

    @property
    def system_data(self) -> dict[str, Any]:
        category = self.categories
        approved = [c for c in self.scan.candidates if c.selectable]
        return {
            "state": ("reconciled" if category.discrepancy_bytes == 0 else "mismatch")
            if category
            else "unavailable",
            "timestamp": category.timestamp if category else None,
            "source": category.source if category else None,
            "native_field": "StorageLogInvestigation - Other" if category else None,
            "native_other_bytes": category.other_bytes if category else None,
            "residual_bytes": category.residual_bytes if category else None,
            "discrepancy_bytes": category.discrepancy_bytes if category else None,
            "approved_candidate_bytes": sum(c.allocated_bytes for c in approved),
            "approved_candidate_count": len(approved),
            "category_membership": "unattributed",
            "space_freed_by_staging": 0,
            "evidence": "Potential contributing files are not proven members of Apple System Data. Trash staging does not free space.",
        }

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["system_data"] = self.system_data
        value["scan"]["candidates"] = [
            {**asdict(c), "selectable": c.selectable} for c in self.scan.candidates
        ]
        return value


@dataclass
class DiskNode:
    path: str
    allocated_bytes: int | None
    is_dir: bool
    depth: int
    complete: bool = True
    age_days: float = 0
    decision: Decision | None = None
    purpose: Decision | None = None


@dataclass
class ExplorationStep:
    path: str
    decision: Decision
    children_seen: int


@dataclass
class ExplorationResult:
    stats: dict[str, Any] = field(default_factory=dict)
    nodes: list[DiskNode] = field(default_factory=list)
    steps: list[ExplorationStep] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    candidates: list[Candidate] = field(default_factory=list)
    complete: bool = True


@dataclass
class MoveResult:
    batch_id: str
    moved: int = 0
    staged_bytes: int = 0
    failed: list[str] = field(default_factory=list)


def human_bytes(value: int | None) -> str:
    if value is None:
        return "unknown"
    for unit, divisor in [("TB", 10**12), ("GB", 10**9), ("MB", 10**6), ("KB", 10**3)]:
        if value >= divisor:
            return f"{value / divisor:.2f} {unit}"
    return f"{value} B"
