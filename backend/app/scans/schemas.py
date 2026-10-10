from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.scan import ScanProfile, ScanStatus


class ScanCreateRequest(BaseModel):
    target: str = Field(..., description="Domain, hostname, or URL to scan")
    profile: ScanProfile = ScanProfile.STANDARD
    scope_config: dict = Field(
        default_factory=dict,
        description="Authorized scope: allowlists, exclusions, etc. Enforced in Phase 4+.",
    )


class ScanResponse(BaseModel):
    id: str
    target: str
    profile: ScanProfile
    status: ScanStatus
    scope_config: dict
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScanEventResponse(BaseModel):
    id: str
    scan_id: str
    event_type: str
    payload: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class AssetResponse(BaseModel):
    id: str
    scan_id: str
    asset_type: str
    value: str
    meta: dict
    discovered_at: datetime

    model_config = {"from_attributes": True}


class FindingResponse(BaseModel):
    id: str
    scan_id: str
    asset_id: Optional[str] = None
    category: str
    severity: str
    confidence: float
    observation: str
    evidence: dict
    remediation: Optional[str] = None
    human_review_required: bool
    created_at: datetime

    model_config = {"from_attributes": True}
