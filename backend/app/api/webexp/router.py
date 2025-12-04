from fastapi import APIRouter

from .endpoints import router as webexp_router


router = APIRouter()

router.include_router(webexp_router, prefix="/webexp", tags=["webexp"])