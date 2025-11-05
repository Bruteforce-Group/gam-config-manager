"""GAM extraction with Server-Sent Events for progress tracking"""
import json
import asyncio
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.db.models import Configuration, ConfigType, SecurityAnalysis
from app.services.gam_service import GAMService
from app.services.security_service import SecurityService

router = APIRouter()


async def extraction_progress_generator(
    config_types: list[ConfigType],
    save_as_template: bool,
    template_name: str | None,
    db: AsyncSession
):
    """Generate Server-Sent Events for extraction progress"""
    
    try:
        # Send initial status
        yield f"data: {json.dumps({'status': 'starting', 'message': 'Initializing GAM extraction...', 'progress': 0})}\n\n"
        await asyncio.sleep(0.5)
        
        gam_service = GAMService()
        results = {}
        errors = []
        total_types = len(config_types)
        
        for idx, config_type in enumerate(config_types, 1):
            progress = int((idx - 0.5) / total_types * 100)
            
            # Send progress for current type
            yield f"data: {json.dumps({'status': 'extracting', 'message': f'Extracting {config_type.value}...', 'current_type': config_type.value, 'progress': progress})}\n\n"
            
            try:
                if config_type == ConfigType.USER:
                    result = await gam_service.extract_users()
                elif config_type == ConfigType.GROUP:
                    result = await gam_service.extract_groups()
                elif config_type == ConfigType.OU:
                    result = await gam_service.extract_org_units()
                elif config_type == ConfigType.DOMAIN:
                    result = await gam_service.extract_domain_settings()
                elif config_type == ConfigType.CALENDAR:
                    result = await gam_service.extract_calendar_settings()
                elif config_type == ConfigType.SECURITY:
                    result = await gam_service.extract_security_settings()
                else:
                    continue
                
                if result["success"]:
                    results[config_type.value] = result["data"]
                    # Count items
                    item_count = len(result["data"]) if isinstance(result["data"], list) else 1
                    message = f'✓ Extracted {item_count} {config_type.value} item(s)'
                    yield f"data: {json.dumps({'status': 'completed_type', 'message': message, 'current_type': config_type.value, 'progress': int(idx / total_types * 100)})}\n\n"
                else:
                    error_msg = result.get('error', 'Unknown error')
                    errors.append(f"{config_type.value}: {error_msg}")
                    message = f'✗ Failed to extract {config_type.value}: {error_msg}'
                    yield f"data: {json.dumps({'status': 'error_type', 'message': message, 'current_type': config_type.value})}\n\n"
            
            except Exception as e:
                error_str = str(e)
                errors.append(f"{config_type.value}: {error_str}")
                message = f'✗ Error extracting {config_type.value}: {error_str}'
                yield f"data: {json.dumps({'status': 'error_type', 'message': message, 'current_type': config_type.value})}\n\n"
        
        if errors:
            yield f"data: {json.dumps({'status': 'partial_error', 'message': f'Completed with {len(errors)} errors', 'errors': errors})}\n\n"
            return
        
        # Save to database
        yield f"data: {json.dumps({'status': 'saving', 'message': 'Saving to database...', 'progress': 90})}\n\n"
        
        config_name = template_name if save_as_template else f"GAM Extract {', '.join(results.keys())}"
        
        db_config = Configuration(
            name=config_name,
            description=f"Extracted from GAM - Types: {', '.join(results.keys())}",
            config_type=config_types[0] if len(config_types) == 1 else ConfigType.OTHER,
            config_data=results,
            is_template=save_as_template
        )
        
        db.add(db_config)
        await db.commit()
        await db.refresh(db_config)
        
        # Automatically run security analysis
        yield f"data: {json.dumps({'status': 'analyzing', 'message': 'Running security analysis...', 'progress': 95})}\n\n"
        
        security_service = SecurityService()
        findings = security_service.analyze_configuration(
            db_config.config_data,
            db_config.config_type
        )
        
        # Save security findings
        findings_count = 0
        for finding in findings:
            db_finding = SecurityAnalysis(
                configuration_id=db_config.id,
                severity=finding["severity"],
                category=finding.get("category"),
                title=finding["title"],
                description=finding["description"],
                recommendation=finding["recommendation"],
                affected_settings=finding.get("affected_settings"),
                remediation_steps=finding.get("remediation_steps")
            )
            db.add(db_finding)
            findings_count += 1
        
        await db.commit()
        
        # Calculate security score
        security_score = security_service.get_security_score(findings)
        
        # Send completion with security score
        total_items = sum(
            len(data) if isinstance(data, list) else 1
            for data in results.values()
        )
        
        completion_msg = f'✓ Extraction complete! Extracted {total_items} items. Security Score: {security_score}/100'
        if findings_count > 0:
            completion_msg += f' ({findings_count} findings)'
        
        yield f"data: {json.dumps({'status': 'complete', 'message': completion_msg, 'configuration_id': db_config.id, 'progress': 100, 'security_score': security_score, 'findings_count': findings_count})}\n\n"
    
    except Exception as e:
        yield f"data: {json.dumps({'status': 'error', 'message': f'Fatal error: {str(e)}'})}\n\n"


@router.get("/extract-stream")
async def extract_gam_config_stream(
    config_types: str = "user,group",  # Comma-separated
    save_as_template: bool = False,
    template_name: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Extract configuration from GAM with Server-Sent Events progress
    
    Query params:
    - config_types: Comma-separated config types (e.g., "user,group")
    - save_as_template: Whether to save as template
    - template_name: Optional template name
    """
    # Parse config types
    type_list = [ConfigType(t.strip()) for t in config_types.split(",")]
    
    return StreamingResponse(
        extraction_progress_generator(type_list, save_as_template, template_name, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

