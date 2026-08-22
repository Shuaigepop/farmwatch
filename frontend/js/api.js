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
export async function apiFetch(endpoint, options = {}) {
  const token = localStorage.getItem('fw_token');
  const headers = {
    ...(options.isForm ? {} : { 'Content-Type': 'application/json' }),
    ...(token && { 'Authorization': `Bearer ${token}` }),
    'ngrok-skip-browser-warning': 'true',
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

    // Handle ngrok interstitial / Method Not Allowed
    if (res.status === 405) {
      const errorMsg = 'Method Not Allowed';
      showToast(errorMsg, 'error');
      throw new Error(errorMsg);
    }

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      let errorMsg;
      if (data.detail) {
        if (typeof data.detail === 'string') errorMsg = data.detail;
        else if (Array.isArray(data.detail)) errorMsg = data.detail.map(e => e.msg).join(', ');
        else errorMsg = JSON.stringify(data.detail);
      } else {
        errorMsg = data.message || 'Unknown error occurred';
      }
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
      headers: { 'Accept': 'application/json', 'ngrok-skip-browser-warning': 'true' }
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
    update: (id, data) => apiFetch(`/farms/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id) => apiFetch(`/farms/${id}`, { method: 'DELETE' }),
    linkGroup: (data) => apiFetch('/farms/link-group', { method: 'POST', body: JSON.stringify(data) }),
    getLineGroups: async () => {
      if (useMock) return [];
      return apiFetch('/farms/line-groups');
    },
    listZones: async (farmId) => {
      if (useMock) return [];
      return apiFetch(`/farms/${farmId}/zones`);
    },
    createZone: (farmId, data) => apiFetch(`/farms/${farmId}/zones`, { method: 'POST', body: JSON.stringify(data) }),
    deleteZone: (zoneId) => apiFetch(`/farms/zones/${zoneId}`, { method: 'DELETE' }),
    listCrops: async (farmId) => apiFetch(`/farms/${farmId}/crops`),
    createCrop: (farmId, data) => apiFetch(`/farms/${farmId}/crops`, { method: 'POST', body: JSON.stringify(data) }),
    updateCrop: (cropId, data) => apiFetch(`/farms/crops/${cropId}`, { method: 'PUT', body: JSON.stringify(data) }),
    deleteCrop: (cropId) => apiFetch(`/farms/crops/${cropId}`, { method: 'DELETE' }),
    plantCrop: (farmId, data) => apiFetch(`/farms/${farmId}/plant`, { method: 'POST', body: JSON.stringify(data) })
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
      if (filters.limit !== undefined) params.append('limit', filters.limit);
      if (filters.offset !== undefined) params.append('offset', filters.offset);
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
      if (filters.target_date) params.append('target_date', filters.target_date);
      if (filters.limit !== undefined) params.append('limit', filters.limit);
      if (filters.offset !== undefined) params.append('offset', filters.offset);
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
      if (filters.zone_id) params.append('zone_id', filters.zone_id);
      return apiFetch(`/tasks/?${params}`);
    },
    create: (data) => apiFetch('/tasks/', { method: 'POST', body: JSON.stringify(data) }),
    update: (id, data) => apiFetch(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id) => apiFetch(`/tasks/${id}`, { method: 'DELETE' })
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
    },
    fertilizerBudget: (farmId, month) => {
      const params = new URLSearchParams();
      if (month) params.append('month', month);
      return apiFetch(`/reports/${farmId}/fertilizer-budget?${params}`);
    }
  },

  inventory: {
    list: async (farmId, filters = {}) => {
      if (!farmId) throw new Error("farmId is required");
      const params = new URLSearchParams();
      if (filters.item_type) params.append('item_type', filters.item_type);
      const queryStr = params.toString() ? `?${params}` : '';
      return apiFetch(`/inventory/${farmId}${queryStr}`);
    },
    create: (farmId, data) => apiFetch(`/inventory/${farmId}`, { method: 'POST', body: JSON.stringify(data) }),
    update: (id, data) => apiFetch(`/inventory/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    delete: (id) => apiFetch(`/inventory/${id}`, { method: 'DELETE' }),
    listHarvest: async (farmId, filters = {}) => {
      if (!farmId) throw new Error("farmId is required");
      const params = new URLSearchParams();
      const queryStr = params.toString() ? `?${params}` : '';
      return apiFetch(`/inventory/harvest/${farmId}${queryStr}`);
    },
    createHarvest: (farmId, data) => apiFetch(`/inventory/harvest/${farmId}`, { method: 'POST', body: JSON.stringify(data) }),
    updateHarvest: (id, data) => apiFetch(`/inventory/harvest/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
    deleteHarvest: (id) => apiFetch(`/inventory/harvest/${id}`, { method: 'DELETE' }),
  }
};
