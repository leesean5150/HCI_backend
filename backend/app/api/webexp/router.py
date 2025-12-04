from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .endpoints import router as webexp_router
from config import settings


# Security scheme - shows "Authorize" button in Swagger UI
security = HTTPBearer()

# Your API key
API_KEY = settings.WEBEXP_API_KEY


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify the bearer token matches the API key.
    """
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    return credentials.credentials


router = APIRouter()

router.include_router(
    webexp_router, 
    prefix="/webexp", 
    tags=["webexp"],
    dependencies=[Depends(verify_token)]
)