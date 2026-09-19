"""Database models"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base


class ConfigType(str, enum.Enum):
    """Configuration types"""
    USER = "user"
    GROUP = "group"
    OU = "organizational_unit"
    DOMAIN = "domain"
    CALENDAR = "calendar"
    DRIVE = "drive"
    GMAIL = "gmail"
    SECURITY = "security"
    MOBILE = "mobile"
    OAUTH_TOKENS = "oauth_tokens"
    ADMIN_ROLES = "admin_roles"
    SHARED_DRIVES = "shared_drives"
    OTHER = "other"


class SeverityLevel(str, enum.Enum):
    """Security severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Configuration(Base):
    """Configuration snapshots"""
    __tablename__ = "configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    config_type = Column(SQLEnum(ConfigType), nullable=False, index=True)
    config_data = Column(JSON, nullable=False)
    is_template = Column(Boolean, default=False, index=True)
    extraction_errors = Column(JSON, nullable=True)  # Store any extraction errors
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    comparisons_as_source = relationship(
        "ConfigComparison",
        foreign_keys="ConfigComparison.source_config_id",
        back_populates="source_config"
    )
    comparisons_as_target = relationship(
        "ConfigComparison",
        foreign_keys="ConfigComparison.target_config_id",
        back_populates="target_config"
    )
    security_analyses = relationship("SecurityAnalysis", back_populates="configuration")
    
    def __repr__(self):
        return f"<Configuration(id={self.id}, name={self.name}, type={self.config_type})>"


class ConfigComparison(Base):
    """Configuration comparison results"""
    __tablename__ = "config_comparisons"
    
    id = Column(Integer, primary_key=True, index=True)
    source_config_id = Column(Integer, ForeignKey("configurations.id"), nullable=False)
    target_config_id = Column(Integer, ForeignKey("configurations.id"), nullable=False)
    differences = Column(JSON, nullable=False)
    drift_detected = Column(Boolean, default=False)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    source_config = relationship(
        "Configuration",
        foreign_keys=[source_config_id],
        back_populates="comparisons_as_source"
    )
    target_config = relationship(
        "Configuration",
        foreign_keys=[target_config_id],
        back_populates="comparisons_as_target"
    )
    
    def __repr__(self):
        return f"<ConfigComparison(id={self.id}, drift={self.drift_detected})>"


class SecurityAnalysis(Base):
    """Security analysis results"""
    __tablename__ = "security_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    configuration_id = Column(Integer, ForeignKey("configurations.id"), nullable=False)
    severity = Column(SQLEnum(SeverityLevel), nullable=False, index=True)
    category = Column(String, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    affected_settings = Column(JSON)
    remediation_steps = Column(JSON)
    remediation_actions = Column(JSON)  # Automated remediation actions
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    configuration = relationship("Configuration", back_populates="security_analyses")
    
    def __repr__(self):
        return f"<SecurityAnalysis(id={self.id}, severity={self.severity})>"


class ConfigTemplate(Base):
    """Configuration templates for best practices"""
    __tablename__ = "config_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(Text)
    config_type = Column(SQLEnum(ConfigType), nullable=False, index=True)
    template_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ConfigTemplate(id={self.id}, name={self.name})>"

