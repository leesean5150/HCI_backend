from fastapi import APIRouter

from .endpoints import router as expenditure_router


router = APIRouter()

router.include_router(expenditure_router, prefix="/expenditure", tags=["expenditure"])