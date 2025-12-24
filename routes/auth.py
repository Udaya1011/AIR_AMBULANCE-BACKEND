# routes/auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Optional

from database.connection import get_collection
from models.user import (
    User, UserCreate, LoginRequest, Token,
    ForgotPasswordRequest, ResetPasswordRequest
)
from utils.auth import (
    verify_password, get_password_hash,
    create_access_token, decode_access_token,
    generate_otp, send_email_otp
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False
)

# ==================================================
# GET CURRENT USER
# ==================================================
async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme)
):
    if request.method == "OPTIONS":
        return None

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )

    token_data = decode_access_token(token)

    if not token_data or "sub" not in token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )

    users_collection = get_collection("users")
    user_data = users_collection.find_one({"email": token_data["sub"]})

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return User(
        id=str(user_data["_id"]),
        email=user_data["email"],
        full_name=user_data["full_name"],
        phone=user_data.get("phone", ""),
        role=user_data["role"],
        is_active=user_data.get("is_active", True),
        profile_picture=user_data.get("profile_picture"),
        created_at=user_data.get("created_at", datetime.utcnow()),
        updated_at=user_data.get("updated_at", datetime.utcnow()),
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
):
    if not current_user or not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return current_user


# ==================================================
# REGISTER
# ==================================================
@router.post("/register", response_model=User)
async def register(user_data: UserCreate):
    users_collection = get_collection("users")

    if users_collection.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = get_password_hash(user_data.password)

    user_dict = user_data.dict()
    user_dict["hashed_password"] = hashed_password
    user_dict.pop("password")
    user_dict["created_at"] = user_dict["updated_at"] = datetime.utcnow()

    result = users_collection.insert_one(user_dict)

    return User(
        id=str(result.inserted_id),
        email=user_dict["email"],
        full_name=user_dict["full_name"],
        phone=user_dict.get("phone", ""),
        role=user_dict["role"],
        is_active=user_dict.get("is_active", True),
        profile_picture=user_dict.get("profile_picture"),
        created_at=user_dict["created_at"],
        updated_at=user_dict["updated_at"],
    )


# ==================================================
# LOGIN
# ==================================================
@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    users_collection = get_collection("users")
    user = users_collection.find_one({"email": login_data.email})

    print(f"DEBUG LOGIN: Email={login_data.email}, UserFound={bool(user)}")

    if not user:
        print("DEBUG LOGIN: User not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    password_valid = verify_password(login_data.password, user.get("hashed_password", ""))
    print(f"DEBUG LOGIN: PasswordValid={password_valid}")

    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Inactive user")

    token_payload = {
        "sub": user["email"],
        "role": user["role"],
        "staff_id": str(user["_id"]),
        "hospital_id": user.get("hospital_id"),
        "hospital_name": user.get("hospital_name")
    }

    access_token = create_access_token(token_payload)

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=User(
            id=str(user["_id"]),
            email=user["email"],
            full_name=user["full_name"],
            phone=user.get("phone", ""),
            role=user["role"],
            is_active=user.get("is_active", True),
            profile_picture=user.get("profile_picture"),
            created_at=user.get("created_at", datetime.utcnow()),
            updated_at=user.get("updated_at", datetime.utcnow()),
        )
    )


# ==================================================
# FORGOT PASSWORD
# ==================================================
@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    users_collection = get_collection("users")
    user = users_collection.find_one({"email": request.email})

    if not user:
        raise HTTPException(status_code=404, detail="Email not found")

    otp = generate_otp()
    expiry = datetime.utcnow() + timedelta(minutes=5)

    users_collection.update_one(
        {"email": request.email},
        {"$set": {"reset_otp": otp, "otp_expiry": expiry}}
    )

    if not send_email_otp(request.email, otp):
        raise HTTPException(status_code=500, detail="Failed to send OTP email")

    return {"message": "OTP sent to email"}


# ==================================================
# RESET PASSWORD
# ==================================================
@router.post("/reset-password")
async def reset_password(data: ResetPasswordRequest):
    users_collection = get_collection("users")
    user = users_collection.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=404, detail="Invalid email")

    if user.get("reset_otp") != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    if user.get("otp_expiry") < datetime.utcnow():
        raise HTTPException(status_code=400, detail="OTP expired")

    hashed_password = get_password_hash(data.new_password)

    users_collection.update_one(
        {"_id": user["_id"]},
        {
            "$set": {
                "hashed_password": hashed_password,
                "updated_at": datetime.utcnow()
            },
            "$unset": {"reset_otp": "", "otp_expiry": ""}
        }
    )

    return {"message": "Password reset successful"}


# ==================================================
# 🔥 OPTIONS HANDLER (THIS FIXES 400)
# ==================================================
@router.options("/{path:path}")
async def auth_options_handler(path: str):
    return Response(status_code=200)
