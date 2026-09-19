"""API v1 router"""
from fastapi import APIRouter
from app.api.v1.endpoints import configurations, comparisons, security, templates, gam, gam_stream, remediation

api_router = APIRouter()

api_router.include_router(
    configurations.router,
    prefix="/configurations",
    tags=["configurations"]
)

api_router.include_router(
    comparisons.router,
    prefix="/comparisons",
    tags=["comparisons"]
)

api_router.include_router(
    security.router,
    prefix="/security",
    tags=["security"]
)

api_router.include_router(
    remediation.router,
    prefix="/remediation",
    tags=["remediation"]
)

api_router.include_router(
    templates.router,
    prefix="/templates",
    tags=["templates"]
)

api_router.include_router(
    gam.router,
    prefix="/gam",
    tags=["gam"]
)

api_router.include_router(
    gam_stream.router,
    prefix="/gam",
    tags=["gam-streaming"]
)

