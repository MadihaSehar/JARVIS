from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.action_proposal import ProposalStatus


class ActionProposalResponse(BaseModel):
    id: str
    scan_id: str
    asset_id: Optional[str] = None
    action_type: str
    rationale: str
    confidence: float
    source: str
    status: ProposalStatus
    policy_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
