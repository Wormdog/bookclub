from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from itsdangerous import SignatureExpired, BadSignature
from .. import models
from ..database import get_db
from ..auth import verify_password, create_access_token, hash_password
from ..schemas import UserRegister, UserOut
from ..config import settings
from ..email_utils import (generate_verify_token, confirm_verify_token,
                           send_verification_email)
 
router = APIRouter(prefix="/auth", tags=["auth"])
 
@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(),
          db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Please verify your email before logging in.")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}
 
@router.post("/register", response_model=UserOut)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    if user_in.invite_code != settings.INVITE_CODE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Invalid invite code.")
    if db.query(models.User).filter(models.User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email already registered.")
    if db.query(models.User).filter(models.User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username already taken.")
    token = generate_verify_token(user_in.email)
    new_user = models.User(
        email=user_in.email, username=user_in.username,
        hashed_password=hash_password(user_in.password),
        is_verified=False, verify_token=token,
    )
    db.add(new_user); db.commit(); db.refresh(new_user)
    try:
        send_verification_email(user_in.email, token)
    except Exception as e:
        print(f"[WARN] Failed to send verification email: {e}")
    return new_user
 
@router.get("/verify", response_class=HTMLResponse)
def verify_email(token: str, db: Session = Depends(get_db)):
    try:
        email = confirm_verify_token(token)
    except SignatureExpired:
        return HTMLResponse("<html><body style='font-family:sans-serif;max-width:480px;"
            "margin:80px auto;text-align:center'><h2>Link Expired</h2>"
            "<p>Your verification link has expired. Please register again.</p>"
            "</body></html>", status_code=400)
    except BadSignature:
        return HTMLResponse("<html><body style='font-family:sans-serif;max-width:480px;"
            "margin:80px auto;text-align:center'><h2>Invalid Link</h2>"
            "<p>This verification link is invalid or already used.</p>"
            "</body></html>", status_code=400)
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return HTMLResponse("<html><body style='font-family:sans-serif;max-width:480px;"
            "margin:80px auto;text-align:center'><h2>Account Not Found</h2>"
            "<p>No account found for this email.</p></body></html>", status_code=404)
    if user.is_verified:
        return HTMLResponse("<html><body style='font-family:sans-serif;max-width:480px;"
            "margin:80px auto;text-align:center'><h2>Already Verified</h2>"
            "<p>Your account is already verified.</p>"
            "<a href='/' style='color:#1E3A5F;font-weight:bold'>Go to Login</a>"
            "</body></html>")
    user.is_verified = True; user.verify_token = None; db.commit()
    return HTMLResponse("<html><body style='font-family:sans-serif;max-width:480px;"
        "margin:80px auto;text-align:center'><h2>Email Verified!</h2>"
        "<p>Your account is confirmed. You can now log in.</p>"
        "<a href='/' style='display:inline-block;margin-top:16px;padding:12px 24px;"
        "background:#1E3A5F;color:#fff;text-decoration:none;"
        "border-radius:6px;font-weight:bold'>Go to Login</a>"
        "</body></html>")

