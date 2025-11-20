from typing import List, Optional
from pydantic import BaseModel

class TimelineItem(BaseModel):
    date: str
    event: str

class RequirementItem(BaseModel):
    category: str  # "case", "qualification", "personnel"
    description: str
    status: str  # "satisfied", "unsatisfied", "manual_check"
    evidence: Optional[str] = None
    score_contribution: float = 0.0 # Optional score if standard exists

class BiddingAnalysisResult(BaseModel):
    requirements: List[RequirementItem]
    
    # AI Tips / Secondary Info
    has_scoring_standard: bool
    total_score_estimate: float
    disqualifiers: List[str]
    timeline: List[TimelineItem]
    suggestions: List[str]
