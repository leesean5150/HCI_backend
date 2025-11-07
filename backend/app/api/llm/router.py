from fastapi import APIRouter

from .endpoints import router as llm_router


router = APIRouter()

router.include_router(llm_router, prefix="/llm", tags=["llm"])