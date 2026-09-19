"""Remediation schemas"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class RemediationAction(BaseModel):
    """Schema for a remediation action"""
    action_id: str
    label: str
    description: str
    gam_command: List[str]
    requires_confirmation: bool = True
    parameters: Optional[Dict[str, Any]] = None


class RemediationRequest(BaseModel):
    """Schema for executing a remediation"""
    finding_id: int
    action_id: str
    parameters: Optional[Dict[str, Any]] = None
    auto_rescan: bool = True


class RemediationResponse(BaseModel):
    """Schema for remediation response"""
    success: bool
    message: str
    finding_id: int
    action_executed: str
    gam_output: Optional[str] = None
    new_configuration_id: Optional[int] = None
    security_score_before: Optional[int] = None
    security_score_after: Optional[int] = None
    finding_resolved: bool = False

