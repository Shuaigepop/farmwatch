cat << 'EOF' > /opt/farmwatch/backend/schemas.py
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class UserBase(BaseModel):
    username: str
    role: str
    display_name: str
    language: str = "zh"
    farm_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class FarmBase(BaseModel):
    name: str
    location: Optional[str] = None
    description: Optional[str] = None

class FarmCreate(FarmBase):
    pass

class FarmResponse(FarmBase):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True

class LineGroupLink(BaseModel):
    line_group_id: str
    farm_id: int
    group_name: Optional[str] = None

class MessageReply(BaseModel):
    reply_to_id: int
    content: str

class MessageSend(BaseModel):
    farm_id: int
    content: str

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    stage: str
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    farm_id: int

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None

class TaskResponse(TaskBase):
    id: int
    farm_id: int
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class PhotoResponse(BaseModel):
    id: int
    message_id: int
    farm_id: Optional[int]
    file_path: str
    thumbnail_path: str
    ai_analysis: Optional[str]
    health_status: str
    captured_at: datetime
    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    line_user_id: Optional[str]
    line_user_name: Optional[str]
    line_group_id: Optional[str]
    farm_id: Optional[int]
    content: Optional[str]
    message_type: str
    image_url: Optional[str]
    is_reply: bool
    created_at: datetime
    class Config:
        from_attributes = True

class PasswordReset(BaseModel):
    new_password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    display_name: Optional[str] = None
    new_password: Optional[str] = None
    role: Optional[str] = None
    farm_id: Optional[int] = None

class LineGroupResponse(BaseModel):
    id: int
    line_group_id: str
    farm_id: Optional[int]
    group_name: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True
EOF
cat << 'EOF' > /opt/farmwatch/backend/routers/auth.py
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
    current_user: User = Depends(require_role(["boss"]))
):
    # 列出所有使用者 (List all users - Boss only)
    result = await db.execute(select(User))
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

EOF
cat << 'EOF' > /opt/farmwatch/frontend/js/api.js
const BASE_URL = '/api';

// ========== Toast 通知 (Toast Notifications) ==========
export function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'error') icon = '❌';

  toast.innerHTML = `<span>${icon}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ========== Fetch 封裝 (Fetch Wrapper) ==========
async function apiFetch(endpoint, options = {}) {
  const token = localStorage.getItem('fw_token');
  const headers = {
    ...(options.isForm ? {} : { 'Content-Type': 'application/json' }),
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers
  };

  try {
    const fetchOptions = { ...options, headers };
    delete fetchOptions.isForm; // 移除自定義屬性

    const res = await fetch(`${BASE_URL}${endpoint}`, fetchOptions);
    
    if (res.status === 401) {
      localStorage.removeItem('fw_token');
      localStorage.removeItem('fw_user');
      window.location.hash = '#/login';
      throw new Error('Unauthorized');
    }

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const errorMsg = data.detail || data.message || 'API Error';
      showToast(errorMsg, 'error');
      throw new Error(errorMsg);
    }

    return data;
  } catch (error) {
    // 只在非已處理的錯誤時顯示 toast
    if (error.message !== 'Unauthorized') {
      console.error(`API Fetch Error [${endpoint}]:`, error);
    }
    throw error;
  }
}

// ========== 判斷是否使用 Mock 模式 ==========
// 如果後端不可用，自動切換到 Mock 模式
let useMock = false;

async function checkBackend() {
  try {
    const res = await fetch(`${BASE_URL}/farms/`, { 
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });
    // 401 means backend is alive but needs auth - that's fine
    useMock = false;
  } catch (e) {
    useMock = true;
    console.warn('⚠️ Backend not available, using mock data');
  }
}

// 啟動時檢查後端 (Check backend on startup)
checkBackend();

// ========== Mock 資料 (Mock Data) ==========
const mockFarms = [
  { id: 1, name: '北谷農場', location: '北區', description: '主要種植生菜和番茄', created_at: '2026-01-01T00:00:00Z' },
  { id: 2, name: '陽光山農場', location: '南區', description: '主要種植農田菜', created_at: '2026-01-01T00:00:00Z' },
  { id: 3, name: '綠野農場', location: '東區', description: '混合蔬菜種植', created_at: '2026-01-01T00:00:00Z' },
];

const mockUsers = {
  admin: { id: 1, username: 'admin', role: 'boss', display_name: '老闆', language: 'zh', farm_id: null },
  supervisor: { id: 2, username: 'supervisor', role: 'supervisor', display_name: '王主管', language: 'zh', farm_id: null },
  leader: { id: 3, username: 'leader', role: 'leader', display_name: '李組長', language: 'zh', farm_id: 1 },
};

const mockPasswords = { admin: 'admin123', supervisor: 'super123', leader: 'leader123' };

const mockMessages = [
  { id: 1, line_user_name: '小陳', farm_id: 1, content: '北谷A區的生菜今天施肥完成了', message_type: 'text', is_reply: false, created_at: new Date(Date.now() - 1800000).toISOString() },
  { id: 2, line_user_name: '老闆', farm_id: 1, content: '收到，辛苦了！', message_type: 'text', is_reply: true, replied_by: 1, created_at: new Date(Date.now() - 1700000).toISOString() },
  { id: 3, line_user_name: '阿明', farm_id: 2, content: '陽光山的番茄有些葉子發黃，拍了照片', message_type: 'text', is_reply: false, created_at: new Date(Date.now() - 3600000).toISOString() },
  { id: 4, line_user_name: '阿明', farm_id: 2, content: '', message_type: 'image', image_url: 'https://images.unsplash.com/photo-1592982537447-6f296d66e7fd?auto=format&fit=crop&w=400&q=60', is_reply: false, created_at: new Date(Date.now() - 3500000).toISOString() },
  { id: 5, line_user_name: '小林', farm_id: 1, content: '今天播種完成了B區', message_type: 'text', is_reply: false, created_at: new Date(Date.now() - 7200000).toISOString() },
];

const mockPhotos = [
  { id: 1, message_id: 4, farm_id: 2, file_path: 'https://images.unsplash.com/photo-1592982537447-6f296d66e7fd?auto=format&fit=crop&w=500&q=60', thumbnail_path: 'https://images.unsplash.com/photo-1592982537447-6f296d66e7fd?auto=format&fit=crop&w=200&q=60', ai_analysis: '{"status": "warning", "notes": "檢測到輕微氮缺乏症狀，建議增施氮肥", "confidence": 0.85}', health_status: 'warning', captured_at: '2026-08-01T10:30:00Z', farm_name: '陽光山農場', uploader: '阿明' },
  { id: 2, message_id: 3, farm_id: 1, file_path: 'https://images.unsplash.com/photo-1586771107445-d3ca888129ff?auto=format&fit=crop&w=500&q=60', thumbnail_path: 'https://images.unsplash.com/photo-1586771107445-d3ca888129ff?auto=format&fit=crop&w=200&q=60', ai_analysis: '{"status": "healthy", "notes": "作物生長狀態良好，土壤濕度適中", "confidence": 0.92}', health_status: 'healthy', captured_at: '2026-08-01T09:15:00Z', farm_name: '北谷農場', uploader: '小陳' },
  { id: 3, message_id: 5, farm_id: 1, file_path: 'https://images.unsplash.com/photo-1574943320219-553eb213f72d?auto=format&fit=crop&w=500&q=60', thumbnail_path: 'https://images.unsplash.com/photo-1574943320219-553eb213f72d?auto=format&fit=crop&w=200&q=60', ai_analysis: '{"status": "healthy", "notes": "播種區域整齊，覆土均勻", "confidence": 0.88}', health_status: 'healthy', captured_at: '2026-07-31T16:00:00Z', farm_name: '北谷農場', uploader: '小林' },
  { id: 4, message_id: 6, farm_id: 3, file_path: 'https://images.unsplash.com/photo-1605000797499-95a51c5269ae?auto=format&fit=crop&w=500&q=60', thumbnail_path: 'https://images.unsplash.com/photo-1605000797499-95a51c5269ae?auto=format&fit=crop&w=200&q=60', ai_analysis: '{"status": "critical", "notes": "發現疑似蟲害痕跡，建議立即檢查並噴灑農藥", "confidence": 0.78}', health_status: 'critical', captured_at: '2026-07-31T14:20:00Z', farm_name: '綠野農場', uploader: '小張' },
  { id: 5, message_id: 7, farm_id: 2, file_path: 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?auto=format&fit=crop&w=500&q=60', thumbnail_path: 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?auto=format&fit=crop&w=200&q=60', ai_analysis: null, health_status: 'pending', captured_at: '2026-08-01T11:45:00Z', farm_name: '陽光山農場', uploader: '阿明' },
  { id: 6, message_id: 8, farm_id: 1, file_path: 'https://images.unsplash.com/photo-1464226184884-fa280b87c399?auto=format&fit=crop&w=500&q=60', thumbnail_path: 'https://images.unsplash.com/photo-1464226184884-fa280b87c399?auto=format&fit=crop&w=200&q=60', ai_analysis: '{"status": "healthy", "notes": "生菜長勢喜人，預計下週可以採收", "confidence": 0.95}', health_status: 'healthy', captured_at: '2026-08-01T08:00:00Z', farm_name: '北谷農場', uploader: '小陳' },
];

const mockTasks = [
  { id: 1, farm_id: 1, title: 'A區生菜施肥', description: '使用有機肥料', stage: 'fertilizing', status: 'completed', created_at: '2026-07-28T00:00:00Z', updated_at: '2026-08-01T10:00:00Z' },
  { id: 2, farm_id: 1, title: 'B區播種', description: '播種番茄苗', stage: 'seeding', status: 'in_progress', created_at: '2026-07-30T00:00:00Z', updated_at: '2026-08-01T08:00:00Z' },
  { id: 3, farm_id: 2, title: '番茄採收', description: '成熟番茄採收', stage: 'harvesting', status: 'pending', created_at: '2026-07-29T00:00:00Z', updated_at: '2026-07-29T00:00:00Z' },
  { id: 4, farm_id: 3, title: '蟲害防治', description: '噴灑有機農藥', stage: 'growing', status: 'in_progress', created_at: '2026-08-01T00:00:00Z', updated_at: '2026-08-01T14:00:00Z' },
];

const mockDailyReports = [
  { id: 1, farm_id: 1, date: '2026-08-01', summary: '北谷農場生長狀態良好，生菜預計下週可採收。需注意A區水分狀況。', generated_at: '2026-08-01T23:55:00Z' },
  { id: 2, farm_id: 2, date: '2026-08-01', summary: '陽光山農場番茄葉片出現發黃現象，疑似輕微氮缺乏。已提醒巡檢人員加強施肥。', generated_at: '2026-08-01T23:55:00Z' },
  { id: 3, farm_id: 3, date: '2026-08-01', summary: '綠野農場發現疑似蟲害，需立即介入處理。整體生長進度延遲。', generated_at: '2026-08-01T23:55:00Z' }
];

// ========== API 物件 (API Object) ==========
export const api = {
  auth: {
    login: async (username, password) => {
      if (useMock) {
        // Mock 登入
        return new Promise((resolve, reject) => {
          setTimeout(() => {
            if (mockPasswords[username] === password) {
              const user = mockUsers[username];
              resolve({ 
                token: 'mock-token-' + username, 
                user: { id: user.id, username: user.username, role: user.role, name: user.display_name, farmId: user.farm_id }
              });
            } else {
              reject(new Error('帳號或密碼錯誤。請使用: admin/admin123, supervisor/super123, leader/leader123'));
            }
          }, 800);
        });
      }
      
      // 真實 API：使用 OAuth2 表單格式 (Real API: use OAuth2 form format)
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);
      
      const res = await fetch(`${BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData
      });
      
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || '登入失敗');
      }
      
      const tokenData = await res.json();
      
      // 取得使用者資料 (Get user info)
      const userRes = await fetch(`${BASE_URL}/auth/me`, {
        headers: { 'Authorization': `Bearer ${tokenData.access_token}` }
      });
      const userData = await userRes.json();
      
      return {
        token: tokenData.access_token,
        user: { 
          id: userData.id, 
          username: userData.username, 
          role: userData.role, 
          name: userData.display_name, 
          farmId: userData.farm_id 
        }
      };
    },
    me: () => apiFetch('/auth/me'),
    register: (userData) => apiFetch('/auth/register', { method: 'POST', body: JSON.stringify(userData) }),
    listUsers: async () => {
      if (useMock) return Object.values(mockUsers);
      return apiFetch('/auth/users');
    },
    resetPassword: (userId, newPassword) => apiFetch(`/auth/users/${userId}/password`, { method: 'PUT', body: JSON.stringify({ new_password: newPassword }) }),
    updateUser: (userId, data) => apiFetch(`/auth/users/${userId}`, { method: 'PUT', body: JSON.stringify(data) }),
    deleteUser: (userId) => apiFetch(`/auth/users/${userId}`, { method: 'DELETE' })
  },

  farms: {
    list: async () => {
      if (useMock) return mockFarms;
      return apiFetch('/farms/');
    },
    stats: (id) => apiFetch(`/farms/${id}/stats`),
    create: (data) => apiFetch('/farms/', { method: 'POST', body: JSON.stringify(data) }),
    delete: (id) => apiFetch(`/farms/${id}`, { method: 'DELETE' }),
    linkGroup: (data) => apiFetch('/farms/link-group', { method: 'POST', body: JSON.stringify(data) }),
    getUnboundGroups: async () => {
      if (useMock) return [];
      return apiFetch('/farms/unbound-groups');
    }
  },

  messages: {
    list: async (filters = {}) => {
      if (useMock) {
        let msgs = [...mockMessages];
        if (filters.farm_id) msgs = msgs.filter(m => m.farm_id === filters.farm_id);
        return msgs;
      }
      const params = new URLSearchParams();
      if (filters.farm_id) params.append('farm_id', filters.farm_id);
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      return apiFetch(`/messages/?${params}`);
    },
    reply: (data) => {
      if (useMock) {
        const newMsg = { id: Date.now(), line_user_name: '老闆', farm_id: data.farm_id || 1, content: data.content, message_type: 'text', is_reply: true, replied_by: 1, created_at: new Date().toISOString() };
        mockMessages.push(newMsg);
        return Promise.resolve(newMsg);
      }
      return apiFetch('/messages/reply', { method: 'POST', body: JSON.stringify(data) });
    },
    send: (data) => {
      if (useMock) {
        const newMsg = { id: Date.now(), line_user_name: '老闆', farm_id: data.farm_id || 1, content: data.content, message_type: 'text', is_reply: true, replied_by: 1, created_at: new Date().toISOString() };
        mockMessages.push(newMsg);
        return Promise.resolve(newMsg);
      }
      return apiFetch('/messages/send', { method: 'POST', body: JSON.stringify(data) });
    }
  },

  photos: {
    list: async (filters = {}) => {
      if (useMock) {
        let photos = [...mockPhotos];
        if (filters.farm_id) photos = photos.filter(p => p.farm_id === filters.farm_id);
        if (filters.health_status) photos = photos.filter(p => p.health_status === filters.health_status);
        return photos;
      }
      const params = new URLSearchParams();
      if (filters.farm_id) params.append('farm_id', filters.farm_id);
      if (filters.health_status) params.append('health_status', filters.health_status);
      return apiFetch(`/photos/?${params}`);
    },
    get: (id) => {
      if (useMock) return Promise.resolve(mockPhotos.find(p => p.id === id));
      return apiFetch(`/photos/${id}`);
    }
  },

  tasks: {
    list: async (filters = {}) => {
      if (useMock) {
        let tasks = [...mockTasks];
        if (filters.farm_id) tasks = tasks.filter(t => t.farm_id === filters.farm_id);
        return tasks;
      }
      const params = new URLSearchParams();
      if (filters.farm_id) params.append('farm_id', filters.farm_id);
      return apiFetch(`/tasks/?${params}`);
    },
    create: (data) => apiFetch('/tasks/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id, data) => apiFetch(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) })
  },

  reports: {
    daily: async (filters = {}) => {
      if (useMock) {
        let reports = [...mockDailyReports];
        if (filters.farm_id) reports = reports.filter(r => r.farm_id === filters.farm_id);
        if (filters.date) reports = reports.filter(r => r.date === filters.date);
        return reports;
      }
      const params = new URLSearchParams();
      if (filters.farm_id) params.append('farm_id', filters.farm_id);
      if (filters.date) params.append('date', filters.date);
      return apiFetch(`/reports/daily?${params}`);
    }
  },

  inventory: {
    list: async (filters = {}) => {
      const params = new URLSearchParams();
      if (filters.farm_id) params.append('farm_id', filters.farm_id);
      if (filters.item_type) params.append('item_type', filters.item_type);
      return apiFetch(`/inventory/?${params}`);
    },
    create: (data) => apiFetch('/inventory/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id, data) => apiFetch(`/inventory/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id) => apiFetch(`/inventory/${id}`, { method: 'DELETE' }),
    listHarvest: async (filters = {}) => {
      const params = new URLSearchParams();
      if (filters.farm_id) params.append('farm_id', filters.farm_id);
      return apiFetch(`/inventory/harvest?${params}`);
    },
    createHarvest: (data) => apiFetch('/inventory/harvest', { method: 'POST', body: JSON.stringify(data) }),
    updateHarvest: (id, data) => apiFetch(`/inventory/harvest/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  }
};
EOF
cat << 'EOF' > /opt/farmwatch/frontend/js/components/settings.js
import { t } from '../i18n.js';
import { auth } from '../auth.js';
import { api, showToast } from '../api.js';

export async function renderSettings(container) {
  const user = auth.getUser();
  if (user.role !== 'boss') {
    container.innerHTML = `<div class="page-container"><h3>Unauthorized</h3><p>Only Boss can access settings.</p></div>`;
    return;
  }

  container.innerHTML = `
    <div class="page-container slide-in">
      <div style="margin-bottom: 2rem;">
        <h2>${t('nav.settings') || 'Settings'}</h2>
        <p class="text-secondary">Manage your farms and system settings.</p>
      </div>
      
      <div style="display: flex; flex-wrap: wrap; gap: 2rem;">
        <!-- Left: Create Form -->
        <div class="glass-panel" style="padding: 2rem; flex: 1; min-width: 300px;">
        <h3 class="section-title">新增农场 (Create New Farm)</h3>
        <p class="text-secondary text-sm" style="margin-bottom: 1.5rem;">
          LINE 群组如果与此处设定的农场名称完全相同，系统将自动绑定讯息。
        </p>
        <form id="create-farm-form" class="flex flex-col gap-4">
          <div class="form-group">
            <label>农场名称 (Farm Name)</label>
            <input type="text" id="farm-name" required placeholder="例如：阳光山农场" class="form-input" style="width: 100%; padding: 0.8rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
          <div class="form-group">
            <label>所在区域 (Location)</label>
            <input type="text" id="farm-location" placeholder="例如：北区" class="form-input" style="width: 100%; padding: 0.8rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
          <div class="form-group">
            <label>备注描述 (Description)</label>
            <textarea id="farm-desc" placeholder="请输入相关说明..." class="form-input" rows="3" style="width: 100%; padding: 0.8rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);"></textarea>
          </div>
          <button type="submit" class="btn btn-primary" id="create-farm-btn" style="padding: 0.8rem; background: var(--primary); color: white; border: none; border-radius: var(--radius-sm); cursor: pointer;">
            建立农场 (Create)
          </button>
        </form>
        </div>
        
        <!-- Right: Farm List -->
        <div class="glass-panel" style="padding: 2rem; flex: 1; min-width: 300px;">
          <h3 class="section-title">现有农场 (Existing Farms)</h3>
          <div id="farm-list-container" style="margin-top: 1rem; max-height: 400px; overflow-y: auto;">
            <div class="skeleton" style="height: 100px; width: 100%;"></div>
          </div>
        </div>
      </div>
      
      <div style="display: flex; flex-wrap: wrap; gap: 2rem; margin-top: 2rem;">
        <!-- User Management -->
        <div class="glass-panel" style="padding: 2rem; flex: 1; min-width: 300px;">
          <h3 class="section-title">使用者管理 (User Management)</h3>
          <div id="user-list-container" style="margin-top: 1rem; max-height: 400px; overflow-y: auto;">
            <div class="skeleton" style="height: 100px; width: 100%;"></div>
          </div>
        </div>
        
        <!-- LINE Integration -->
        <div class="glass-panel" style="padding: 2rem; flex: 1; min-width: 300px;">
          <h3 class="section-title">LINE 群组绑定 (LINE Integration)</h3>
          <p class="text-secondary text-sm" style="margin-bottom: 1rem;">手动将未识别的 LINE 群组绑定到农场。</p>
          <div id="unbound-groups-container" style="margin-top: 1rem; max-height: 400px; overflow-y: auto;">
            <div class="skeleton" style="height: 100px; width: 100%;"></div>
          </div>
        </div>
      </div>
    </div>
  `;

  await loadFarmList();
  await loadUserList();
  await loadUnboundGroups();

  document.getElementById('create-farm-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('create-farm-btn');
    const name = document.getElementById('farm-name').value;
    const location = document.getElementById('farm-location').value;
    const description = document.getElementById('farm-desc').value;

    btn.disabled = true;
    btn.textContent = '建立中 (Creating)...';

    try {
      await api.farms.create({ name, location, description });
      showToast('✅ 农场建立成功！(Farm created successfully)', 'success');
      document.getElementById('create-farm-form').reset();
      await loadFarmList(); // Refresh list
    } catch (err) {
      showToast('❌ 建立失败 (Failed to create farm)', 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = '建立农场 (Create)';
    }
  });
}

async function loadFarmList() {
  const container = document.getElementById('farm-list-container');
  if (!container) return;
  
  try {
    const farms = await api.farms.list();
    if (!farms || farms.length === 0) {
      container.innerHTML = `<p class="text-secondary text-sm">目前没有任何农场。</p>`;
      return;
    }
    
    container.innerHTML = farms.map(farm => `
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem; border-bottom: 1px solid var(--border-color);">
        <div>
          <div style="font-weight: 600;">${farm.name}</div>
          <div class="text-secondary text-sm">${farm.location || '未定区域'}</div>
        </div>
        <button class="icon-btn delete-farm-btn" data-id="${farm.id}" style="color: var(--danger);" title="删除农场">🗑️</button>
      </div>
    `).join('');
    
    // Add delete event listeners
    document.querySelectorAll('.delete-farm-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const farmId = e.currentTarget.dataset.id;
        if (confirm('确定要删除这个农场吗？此操作无法撤销。')) {
          try {
            await api.farms.delete(farmId);
            showToast('✅ 农场已删除', 'success');
            await loadFarmList(); // Refresh list
            await loadUnboundGroups(); // Also refresh dropdowns
          } catch(err) {
            showToast('❌ 删除失败', 'error');
          }
        }
      });
    });
  } catch (e) {
    container.innerHTML = `<p style="color: var(--danger)">无法载入农场列表</p>`;
  }
}

async function loadUserList() {
  const container = document.getElementById('user-list-container');
  if (!container) return;
  
  try {
    const users = await api.auth.listUsers();
    const farms = await api.farms.list();
    if (!users || users.length === 0) {
      container.innerHTML = `<p class="text-secondary text-sm">目前没有任何使用者。</p>`;
      return;
    }
    
    const farmOptions = farms.map(f => `<option value="${f.id}">${f.name}</option>`).join('');
    
    let html = users.map(u => `
      <div style="padding: 1rem; border-bottom: 1px solid var(--border-color);" id="user-card-${u.id}">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
          <span class="badge badge-info">${u.role}</span>
          ${users.length > 1 ? `<button class="icon-btn delete-user-btn" data-id="${u.id}" data-name="${u.display_name}" style="color: var(--danger); font-size: 1.2rem;" title="删除此使用者">🗑️</button>` : ''}
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
          <div>
            <label class="text-secondary text-sm">显示名称</label>
            <input type="text" id="uname-${u.id}" value="${u.display_name}" class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
          <div>
            <label class="text-secondary text-sm">登入帐号</label>
            <input type="text" id="ulogin-${u.id}" value="${u.username}" class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
          <div>
            <label class="text-secondary text-sm">新密码 (留空不改)</label>
            <input type="password" id="upw-${u.id}" placeholder="输入新密码..." class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
          <div>
            <label class="text-secondary text-sm">角色</label>
            <select id="urole-${u.id}" class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
              <option value="boss" ${u.role === 'boss' ? 'selected' : ''}>老闆 (Boss)</option>
              <option value="supervisor" ${u.role === 'supervisor' ? 'selected' : ''}>主管 (Supervisor)</option>
              <option value="leader" ${u.role === 'leader' ? 'selected' : ''}>組長 (Leader)</option>
            </select>
          </div>
        </div>
        <button class="btn btn-secondary save-user-btn" data-id="${u.id}" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); cursor: pointer; margin-top: 0.3rem;">
          💾 储存变更 (Save)
        </button>
      </div>
    `).join('');
    
    // Add New User form
    html += `
      <div style="padding: 1.2rem; border-top: 2px solid var(--primary); margin-top: 0.5rem; background: rgba(45,80,22,0.05); border-radius: 0 0 var(--radius-md) var(--radius-md);">
        <h4 style="margin-bottom: 0.8rem; color: var(--primary);">➕ 新增使用者 (Add New User)</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
          <div>
            <label class="text-secondary text-sm">显示名称</label>
            <input type="text" id="new-user-name" placeholder="例如：张三" class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
          <div>
            <label class="text-secondary text-sm">登入帐号</label>
            <input type="text" id="new-user-login" placeholder="例如：zhangsan" class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
          <div>
            <label class="text-secondary text-sm">密码</label>
            <input type="password" id="new-user-pw" placeholder="设定密码" class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
          <div>
            <label class="text-secondary text-sm">角色</label>
            <select id="new-user-role" class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
              <option value="leader">組長 (Leader)</option>
              <option value="supervisor">主管 (Supervisor)</option>
              <option value="boss">老闆 (Boss)</option>
            </select>
          </div>
        </div>
        <button class="btn btn-primary" id="add-user-btn" style="width: 100%; padding: 0.6rem; background: var(--primary); color: white; border: none; border-radius: var(--radius-sm); cursor: pointer;">
          新增使用者 (Create User)
        </button>
      </div>
    `;
    
    container.innerHTML = html;
    
    // Save user changes
    document.querySelectorAll('.save-user-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const userId = e.currentTarget.dataset.id;
        const displayName = document.getElementById(`uname-${userId}`).value.trim();
        const username = document.getElementById(`ulogin-${userId}`).value.trim();
        const newPw = document.getElementById(`upw-${userId}`).value;
        const role = document.getElementById(`urole-${userId}`).value;
        
        if (!displayName || !username) {
          showToast('❌ 名称和帐号不能为空', 'error');
          return;
        }
        
        btn.disabled = true;
        btn.textContent = '储存中...';
        try {
          const updateData = { username, display_name: displayName, role };
          if (newPw) updateData.new_password = newPw;
          await api.auth.updateUser(userId, updateData);
          showToast('✅ 使用者资料已更新', 'success');
          document.getElementById(`upw-${userId}`).value = '';
          await loadUserList();
        } catch(err) {
          showToast('❌ 更新失败: ' + (err.message || ''), 'error');
        } finally {
          btn.disabled = false;
          btn.textContent = '💾 储存变更 (Save)';
        }
      });
    });
    
    // Delete user
    document.querySelectorAll('.delete-user-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const userId = e.currentTarget.dataset.id;
        const userName = e.currentTarget.dataset.name;
        if (!confirm(`确定要删除使用者「${userName}」吗？此操作无法撤销。`)) return;
        
        try {
          await api.auth.deleteUser(userId);
          showToast('✅ 使用者已删除', 'success');
          await loadUserList();
        } catch(err) {
          showToast('❌ 删除失败: ' + (err.message || ''), 'error');
        }
      });
    });
    
    // Add new user
    document.getElementById('add-user-btn')?.addEventListener('click', async () => {
      const displayName = document.getElementById('new-user-name').value.trim();
      const username = document.getElementById('new-user-login').value.trim();
      const password = document.getElementById('new-user-pw').value;
      const role = document.getElementById('new-user-role').value;
      
      if (!displayName || !username || !password) {
        showToast('❌ 请填写所有栏位', 'error');
        return;
      }
      
      const btn = document.getElementById('add-user-btn');
      btn.disabled = true;
      btn.textContent = '新增中...';
      try {
        await api.auth.register({ username, password, role, display_name: displayName, language: 'zh' });
        showToast('✅ 使用者新增成功！', 'success');
        await loadUserList();
      } catch(err) {
        showToast('❌ 新增失败: ' + (err.message || ''), 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = '新增使用者 (Create User)';
      }
    });
  } catch (e) {
    container.innerHTML = `<p style="color: var(--danger)">无法载入使用者</p>`;
  }
}


async function loadUnboundGroups() {
  const container = document.getElementById('unbound-groups-container');
  if (!container) return;
  
  try {
    const groups = await api.farms.getUnboundGroups();
    const farms = await api.farms.list();
    
    if (!groups || groups.length === 0) {
      container.innerHTML = `<p class="text-secondary text-sm">目前没有未绑定的群组。</p>`;
      return;
    }
    
    const farmOptions = farms.map(f => `<option value="${f.id}">${f.name}</option>`).join('');
    
    container.innerHTML = groups.map(g => `
      <div style="padding: 1rem; border-bottom: 1px solid var(--border-color);">
        <div style="margin-bottom: 0.5rem; font-weight: 600;">
          群组名称: ${g.group_name || '未知名称 (Unknown)'}
        </div>
        <div class="text-secondary text-sm" style="margin-bottom: 0.5rem; word-break: break-all;">
          ID: ${g.line_group_id}
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <select id="bind-farm-${g.line_group_id}" class="form-input" style="flex: 1; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
            <option value="">选择农场 (Select Farm)...</option>
            ${farmOptions}
          </select>
          <button class="btn btn-primary bind-group-btn" data-group="${g.line_group_id}" data-name="${g.group_name || ''}" style="padding: 0.5rem 1rem; background: var(--primary); color: white; border: none; border-radius: var(--radius-sm); cursor: pointer;">
            绑定 (Bind)
          </button>
        </div>
      </div>
    `).join('');
    
    document.querySelectorAll('.bind-group-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const groupId = e.currentTarget.dataset.group;
        const groupName = e.currentTarget.dataset.name;
        const farmIdStr = document.getElementById(`bind-farm-${groupId}`).value;
        
        if (!farmIdStr) {
          showToast('❌ 请选择一个农场 (Select a farm)', 'error');
          return;
        }
        
        const farmId = parseInt(farmIdStr, 10);
        btn.disabled = true;
        
        try {
          await api.farms.linkGroup({ line_group_id: groupId, farm_id: farmId, group_name: groupName });
          showToast('✅ 绑定成功！(Bound successfully)', 'success');
          await loadUnboundGroups(); // Refresh
        } catch(err) {
          showToast('❌ 绑定失败 (Failed)', 'error');
          btn.disabled = false;
        }
      });
    });
  } catch (e) {
    container.innerHTML = `<p style="color: var(--danger)">无法载入未绑定群组</p>`;
  }
}
EOF
cd /opt/farmwatch && docker compose build && docker compose up -d
