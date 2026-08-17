from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from passlib.context import CryptContext
from jose import jwt

from config import settings
from models.models import User
from typing import List
from schemas import UserCreate, UserResponse, Token, PasswordReset, UserUpdate
from deps import get_db, get_current_user, require_role

router = APIRouter(prefix="/api/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # 使用者登入 (User login)
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role, "id": user.id}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    # 取得當前使用者 (Get current user)
    return current_user

@router.post("/register", response_model=UserResponse)
async def register(
    user_in: UserCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss"]))
):
    # 註冊新使用者 - 僅限老闆 (Register new user - Boss only)
    result = await db.execute(select(User).where(User.username == user_in.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already registered")
        
    new_user = User(
        username=user_in.username,
        password_hash=pwd_context.hash(user_in.password),
        role=user_in.role,
        display_name=user_in.display_name,
        language=user_in.language,
        farm_id=user_in.farm_id
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss", "supervisor"]))
):
    # 列出所有使用者 (List all users - Boss and Supervisor)
    query = select(User)
    if current_user.role != "boss" and current_user.farm_id:
        query = query.where(User.farm_id == current_user.farm_id)
    result = await db.execute(query)
    return result.scalars().all()

@router.put("/users/{user_id}/password")
async def reset_password(
    user_id: int,
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss"]))
):
    # 重設使用者密碼 (Reset user password - Boss only)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.password_hash = pwd_context.hash(reset_data.new_password)
    await db.commit()
    return {"status": "success"}

@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss"]))
):
    # 更新使用者資料 (Update user info - Boss only)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # 更新使用者名稱 (Update username)
    if update_data.username and update_data.username != user.username:
        existing = await db.execute(select(User).where(User.username == update_data.username))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Username already taken")
        user.username = update_data.username
    
    # 更新顯示名稱 (Update display name)
    if update_data.display_name:
        user.display_name = update_data.display_name
    
    # 更新密碼 (Update password)
    if update_data.new_password:
        user.password_hash = pwd_context.hash(update_data.new_password)
    
    # 更新角色 (Update role)
    if update_data.role and update_data.role in ["boss", "supervisor", "leader"]:
        user.role = update_data.role
    
    # 更新農場 (Update farm)
    if update_data.farm_id is not None:
        user.farm_id = update_data.farm_id if update_data.farm_id > 0 else None
    
    await db.commit()
    await db.refresh(user)
    return {"status": "success", "user": {"id": user.id, "username": user.username, "display_name": user.display_name, "role": user.role}}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(["boss"]))
):
    # 刪除使用者 - 至少保留一個 (Delete user - must keep at least one)
    total = await db.scalar(select(func.count(User.id)))
    if total <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the last user")
    
    # 不能刪除自己 (Cannot delete yourself)
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await db.delete(user)
    await db.commit()
    return {"status": "success"}

