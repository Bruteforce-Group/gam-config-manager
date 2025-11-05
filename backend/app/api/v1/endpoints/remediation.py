"""Remediation endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.base import get_db
from app.db.models import Configuration, SecurityAnalysis, ConfigType
from app.schemas.remediation import RemediationRequest, RemediationResponse
from app.services.gam_service import GAMService
from app.services.security_service import SecurityService

router = APIRouter()


@router.post("/execute", response_model=RemediationResponse)
async def execute_remediation(
    request: RemediationRequest,
    db: AsyncSession = Depends(get_db)
):
    """Execute a remediation action"""
    # Get the finding
    result = await db.execute(
        select(SecurityAnalysis).where(SecurityAnalysis.id == request.finding_id)
    )
    finding = result.scalar_one_or_none()
    
    if not finding:
        raise HTTPException(status_code=404, detail="Security finding not found")
    
    # Get the configuration
    config_result = await db.execute(
        select(Configuration).where(Configuration.id == finding.configuration_id)
    )
    config = config_result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    # Get current security score
    score_before_result = await db.execute(
        select(SecurityAnalysis).where(SecurityAnalysis.configuration_id == finding.configuration_id)
    )
    analyses_before = score_before_result.scalars().all()
    security_service = SecurityService()
    score_before = security_service.get_security_score([{"severity": a.severity} for a in analyses_before])
    
    # Extract GAM command from finding's remediation_actions
    # Note: In production, you'd parse this from the stored finding
    # For now, we'll construct based on action_id
    gam_service = GAMService()
    
    # Execute the GAM command based on action_id
    if request.action_id == "enforce_2fa":
        user_email = request.parameters.get("user_email")
        if not user_email:
            raise HTTPException(status_code=400, detail="user_email parameter required")
        
        gam_result = await gam_service._run_gam_command([
            "update", "user", user_email, "enforcein2sv", "true"
        ])
    
    elif request.action_id == "revoke_oauth_token":
        user = request.parameters.get("user")
        client_id = request.parameters.get("client_id")
        if not user or not client_id:
            raise HTTPException(status_code=400, detail="user and client_id parameters required")
        
        gam_result = await gam_service._run_gam_command([
            "user", user, "revoke", "token", client_id
        ])
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action_id: {request.action_id}")
    
    if not gam_result["success"]:
        return RemediationResponse(
            success=False,
            message=f"Remediation failed: {gam_result.get('error')}",
            finding_id=request.finding_id,
            action_executed=request.action_id,
            gam_output=gam_result.get("error"),
            finding_resolved=False
        )
    
    # If auto_rescan is enabled, extract fresh config and re-analyze
    new_config_id = None
    score_after = None
    finding_resolved = False
    
    if request.auto_rescan:
        # Determine which config type to re-extract based on the finding
        config_types_to_extract = []
        
        if request.action_id == "enforce_2fa":
            config_types_to_extract = [ConfigType.USER]
        elif request.action_id == "revoke_oauth_token":
            config_types_to_extract = [ConfigType.OAUTH_TOKENS]
        
        # Extract fresh configuration
        if config_types_to_extract:
            extract_result = await gam_service.extract_all_configs(config_types_to_extract)
            
            if extract_result["success"]:
                # Save new configuration
                new_config = Configuration(
                    name=f"Post-Remediation: {config.name}",
                    description=f"Re-extracted after fixing: {finding.title}",
                    config_type=config_types_to_extract[0] if len(config_types_to_extract) == 1 else ConfigType.OTHER,
                    config_data=extract_result["data"],
                    is_template=False
                )
                db.add(new_config)
                await db.commit()
                await db.refresh(new_config)
                new_config_id = new_config.id
                
                # Run security analysis on new config
                new_findings = security_service.analyze_configuration(
                    new_config.config_data,
                    new_config.config_type
                )
                
                # Save new findings
                for new_finding in new_findings:
                    db_finding = SecurityAnalysis(
                        configuration_id=new_config_id,
                        severity=new_finding["severity"],
                        category=new_finding.get("category"),
                        title=new_finding["title"],
                        description=new_finding["description"],
                        recommendation=new_finding["recommendation"],
                        affected_settings=new_finding.get("affected_settings"),
                        remediation_steps=new_finding.get("remediation_steps")
                    )
                    db.add(db_finding)
                
                await db.commit()
                
                # Calculate new security score
                score_after = security_service.get_security_score(new_findings)
                
                # Check if the specific finding is resolved
                finding_resolved = not any(
                    f["title"] == finding.title and 
                    f.get("affected_settings") == finding.affected_settings
                    for f in new_findings
                )
    
    return RemediationResponse(
        success=True,
        message="Remediation executed successfully" + (" and verified" if finding_resolved else ""),
        finding_id=request.finding_id,
        action_executed=request.action_id,
        gam_output=gam_result.get("data"),
        new_configuration_id=new_config_id,
        security_score_before=score_before,
        security_score_after=score_after,
        finding_resolved=finding_resolved
    )

