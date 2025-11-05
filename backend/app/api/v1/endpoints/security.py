"""Security analysis endpoints"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.db.models import Configuration, SecurityAnalysis
from app.schemas.config import SecurityAnalysisResponse
from app.services.security_service import SecurityService

router = APIRouter()


@router.post("/analyze/{config_id}", response_model=List[SecurityAnalysisResponse])
async def analyze_configuration(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Analyze a configuration for security issues"""
    # Get configuration
    result = await db.execute(
        select(Configuration).where(Configuration.id == config_id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    # Delete existing security analyses for this configuration (prevent duplicates)
    existing_analyses = await db.execute(
        select(SecurityAnalysis).where(SecurityAnalysis.configuration_id == config_id)
    )
    for existing in existing_analyses.scalars():
        await db.delete(existing)
    
    # Perform security analysis
    security_service = SecurityService()
    findings = security_service.analyze_configuration(
        config.config_data,
        config.config_type
    )
    
    # Save new findings
    db_findings = []
    for finding in findings:
        db_finding = SecurityAnalysis(
            configuration_id=config_id,
            severity=finding["severity"],
            category=finding.get("category"),
            title=finding["title"],
            description=finding["description"],
            recommendation=finding["recommendation"],
            affected_settings=finding.get("affected_settings"),
            remediation_steps=finding.get("remediation_steps"),
            remediation_actions=finding.get("remediation_actions")
        )
        db.add(db_finding)
        db_findings.append(db_finding)
    
    await db.commit()
    
    # Refresh all findings
    for finding in db_findings:
        await db.refresh(finding)
    
    return db_findings


@router.get("/analyses/{config_id}", response_model=List[SecurityAnalysisResponse])
async def get_security_analyses(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get all security analyses for a configuration"""
    result = await db.execute(
        select(SecurityAnalysis)
        .where(SecurityAnalysis.configuration_id == config_id)
        .order_by(SecurityAnalysis.severity, SecurityAnalysis.created_at.desc())
    )
    analyses = result.scalars().all()
    return analyses


@router.get("/score/{config_id}")
async def get_security_score(
    config_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get security score for a configuration"""
    result = await db.execute(
        select(SecurityAnalysis)
        .where(SecurityAnalysis.configuration_id == config_id)
    )
    analyses = result.scalars().all()
    
    # Calculate score
    security_service = SecurityService()
    findings_data = [
        {"severity": analysis.severity}
        for analysis in analyses
    ]
    score = security_service.get_security_score(findings_data)
    
    return {
        "configuration_id": config_id,
        "security_score": score,
        "total_findings": len(analyses),
        "critical_findings": sum(1 for a in analyses if a.severity == "critical"),
        "high_findings": sum(1 for a in analyses if a.severity == "high"),
        "medium_findings": sum(1 for a in analyses if a.severity == "medium"),
        "low_findings": sum(1 for a in analyses if a.severity == "low"),
    }

