from typing import List, Optional
from pydantic import BaseModel

class TimelineItem(BaseModel):
    date: str
    event: str

class BiddingAnalysisResult(BaseModel):
    totalScore: int
    businessScore: int
    techScore: int
    disqualifiers: List[str]
    timeline: List[TimelineItem]
    suggestions: List[str]
    scoreDetails: Optional[str] = None
