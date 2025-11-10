from fastapi import APIRouter

from .expenditure.router import router as expenditure_router
from .llm.router import router as llm_router
from .user.router import router as user_router


router = APIRouter()

router.include_router(expenditure_router)
router.include_router(llm_router)
router.include_router(user_router)