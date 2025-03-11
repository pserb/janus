from fastapi import APIRouter

from .endpoints import jobs, companies, sources, stats

# Create API router
api_router = APIRouter()

# Include all API endpoints
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
