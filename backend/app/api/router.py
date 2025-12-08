from fastapi import APIRouter

from .expenditure.router import router as expenditure_router
from .llm.router import router as llm_router
from .user.router import router as user_router
from .webexp.router import router as webexp_router
from .insights.router import router as insights_router


router = APIRouter()

router.include_router(expenditure_router)
router.include_router(llm_router)
router.include_router(user_router)
router.include_router(webexp_router)
router.include_router(insights_router)