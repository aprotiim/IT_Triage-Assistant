from typing import Literal

from pydantic import BaseModel


class AccessCheckResult(BaseModel):
    user_email: str
    resource: str
    has_access: bool
    reason: str
    checked_at: str


class VpnResetResult(BaseModel):
    user_email: str
    status: Literal["success"]
    credentials_expire_at: str
    message: str


class AssetStatus(BaseModel):
    asset_tag: str
    owner_email: str
    status: Literal["active", "in_repair", "retired"]
    last_seen: str
    battery_health_pct: int | None = None
    notes: str = ""


class LicenseApprovalResult(BaseModel):
    request_id: str
    user_email: str
    software_name: str
    status: Literal["approved", "denied", "pending_manager_review"]
    reason: str
