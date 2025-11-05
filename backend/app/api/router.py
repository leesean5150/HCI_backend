from fastapi import APIRouter

from .expenditure.router import router as expenditure_router


router = APIRouter()

router.include_router(expenditure_router)