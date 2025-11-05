"""Configuration schemas"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.db.models import ConfigType, SeverityLevel


class ConfigurationBase(BaseModel):
    """Base configuration schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    config_type: ConfigType
    config_data: Dict[str, Any]
    is_template: bool = False


class ConfigurationCreate(ConfigurationBase):
    """Schema for creating a configuration"""
    pass


class ConfigurationUpdate(BaseModel):
    """Schema for updating a configuration"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    config_data: Optional[Dict[str, Any]] = None
    is_template: Optional[bool] = None


class ConfigurationResponse(ConfigurationBase):
    """Schema for configuration response"""
    id: int
    extraction_errors: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ConfigComparisonCreate(BaseModel):
    """Schema for creating a configuration comparison"""
    source_config_id: int
    target_config_id: int


class ConfigComparisonResponse(BaseModel):
    """Schema for comparison response"""
    id: int
    source_config_id: int
    target_config_id: int
    differences: Dict[str, Any]
    drift_detected: bool
    summary: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SecurityAnalysisResponse(BaseModel):
    """Schema for security analysis response"""
    id: int
    configuration_id: int
    severity: SeverityLevel
    category: Optional[str]
    title: str
    description: str
    recommendation: str
    affected_settings: Optional[Dict[str, Any]]
    remediation_steps: Optional[List[str]]
    remediation_actions: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConfigTemplateBase(BaseModel):
    """Base template schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    config_type: ConfigType
    template_data: Dict[str, Any]
    is_active: bool = True


class ConfigTemplateCreate(ConfigTemplateBase):
    """Schema for creating a template"""
    pass


class ConfigTemplateResponse(ConfigTemplateBase):
    """Schema for template response"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GAMExtractRequest(BaseModel):
    """Schema for GAM extraction request"""
    config_types: List[ConfigType] = Field(default_factory=lambda: [ConfigType.USER, ConfigType.GROUP])
    save_as_template: bool = False
    template_name: Optional[str] = None


class GAMExtractResponse(BaseModel):
    """Schema for GAM extraction response"""
    success: bool
    message: str
    configuration_id: Optional[int] = None
    extracted_types: List[ConfigType]
    total_items: int
    errors: Optional[List[str]] = None
    failed_types: Optional[List[ConfigType]] = None

