"""GAM extraction endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.db.models import Configuration, ConfigType, SecurityAnalysis
from app.schemas.config import GAMExtractRequest, GAMExtractResponse
from app.services.gam_service import GAMService
from app.services.security_service import SecurityService

router = APIRouter()


@router.post("/extract", response_model=GAMExtractResponse)
async def extract_gam_config(
    request: GAMExtractRequest,
    db: AsyncSession = Depends(get_db)
):
    """Extract configuration from GAM"""
    gam_service = GAMService()
    
    # Extract configurations
    result = await gam_service.extract_all_configs(request.config_types)
    
    errors = result.get("errors", [])
    
    if not result["success"] and not result["data"]:
        # Total failure - no data extracted at all
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract configurations: {errors}"
        )
    
    # Count total items
    total_items = sum(
        len(data) if isinstance(data, list) else 1
        for data in result["data"].values()
    )
    
    # Determine which types failed
    failed_types = [t for t in request.config_types if t.value not in result["data"]]
    
    # Save to database
    config_name = request.template_name if request.save_as_template else f"GAM Extract {', '.join(result['data'].keys())}"
    
    db_config = Configuration(
        name=config_name,
        description=f"Extracted from GAM - Types: {', '.join([t.value for t in request.config_types])}",
        config_type=request.config_types[0] if len(request.config_types) == 1 else ConfigType.OTHER,
        config_data=result["data"],
        is_template=request.save_as_template,
        extraction_errors={"errors": errors, "failed_types": [t.value for t in failed_types]} if errors else None
    )
    
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)
    
    # Automatically run security analysis on the extracted configuration
    security_service = SecurityService()
    findings = security_service.analyze_configuration(
        db_config.config_data,
        db_config.config_type
    )
    
    # Save security findings
    for finding in findings:
        db_finding = SecurityAnalysis(
            configuration_id=db_config.id,
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
    
    await db.commit()
    
    return GAMExtractResponse(
        success=True,
        message="Configuration extracted successfully" if not errors else f"Partially extracted ({len(errors)} errors)",
        configuration_id=db_config.id,
        extracted_types=request.config_types,
        total_items=total_items,
        errors=errors if errors else None,
        failed_types=failed_types if failed_types else None
    )


@router.get("/test-connection")
async def test_gam_connection():
    """Test GAM connection"""
    gam_service = GAMService()
    
    # Try a simple command
    result = await gam_service._run_gam_command(["version"])
    
    if result["success"]:
        return {
            "status": "connected",
            "message": "GAM is properly configured",
            "version": result["data"]
        }
    else:
        return {
            "status": "error",
            "message": f"Failed to connect to GAM: {result['error']}"
        }

