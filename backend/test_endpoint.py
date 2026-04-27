from fastapi import APIRouter, Depends
from app.middleware.auth_middleware import get_current_user

router = APIRouter()

@router.get("/api/v1/test-endpoint")
def test_endpoint(current_user: dict = Depends(get_current_user)):
    """Test endpoint to verify auth works."""
    return {
        "status": "success",
        "message": "Auth working!",
        "user_email": current_user.get("email")
    }
