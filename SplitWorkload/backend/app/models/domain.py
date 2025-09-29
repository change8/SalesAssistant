from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class RequirementRecord:
    """Normalized requirement information extracted from the spreadsheet."""

    identifier: Optional[str]
    project: Optional[str]
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SheetPayload:
    """Container for sheet-level inputs and metadata."""

    name: str
    requirements: List[RequirementRecord]
    total_constraint: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class RequirementAllocation:
    """Represents an allocation outcome for a single requirement."""

    requirement: RequirementRecord
    allocation: Dict[str, float]
    analysis: Optional[str] = None


@dataclass(slots=True)
class SheetAllocation:
    """Allocation outcomes for an entire sheet."""

    sheet: SheetPayload
    allocations: List[RequirementAllocation]
    summary: Dict[str, Any]
