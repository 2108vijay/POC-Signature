from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from SRC.auth.jwt_handler import create_token
from SRC.auth.users import authenticate_user

router = APIRouter(tags=["Authentication"])


@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not authenticate_user(form_data.username, form_data.password):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    token = create_token(form_data.username)
    return {
        "access_token": token,
        "token_type":   "bearer",
    }