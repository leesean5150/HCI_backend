from fastapi import APIRouter

from .endpoints import router as insights_router


router = APIRouter()

router.include_router(insights_router, prefix="/insights", tags=["insights"])