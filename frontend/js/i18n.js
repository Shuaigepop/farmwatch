const translations = {
  en: {
    // Navigation
    nav: {
      dashboard: "Dashboard",
      photoWall: "Photo Wall",
      messages: "Messages",
      progress: "Tasks & Schedule",
      healthReport: "Health Report",
      dailySummary: "Daily Summary",
      settings: "Settings",
      inventory: "Inventory"
    },
    // Login
    login: {
      title: "FarmWatch",
      subtitle: "Premium Farm Management",
      username: "Username",
      password: "Password",
      loginBtn: "Login",
      loading: "Authenticating..."
    },
    // Dashboard
    dashboard: {
      welcome: "Welcome back",
      totalFarms: "Total Farms",
      todayMessages: "Today's Messages",
      todayPhotos: "Today's Photos",
      activeTasks: "Active Tasks",
      recentActivity: "Recent Activity",
      recentPhotos: "Recent Photos",
      quickActions: "Quick Actions"
    },
    // Common
    common: {
      filter: "Filter",
      search: "Search...",
      all: "All",
      today: "Today",
      thisWeek: "This Week",
      save: "Save",
      cancel: "Cancel",
      reply: "Reply",
      send: "Send",
      logout: "Logout",
      loading: "Loading...",
      noData: "No data available."
    },
    // Roles
    roles: {
      boss: "Boss",
      supervisor: "Supervisor",
      leader: "Leader"
    },
    // Health
    health: {
      healthy: "Healthy",
      warning: "Warning",
      critical: "Critical",
      pending: "Pending Analysis"
    },
    // Stages
    stages: {
      seeding: "Seeding",
      fertilizing: "Fertilizing",
      growing: "Growing",
      harvesting: "Harvesting"
    },
    // Photo Wall
    photos: {
      title: "Photo Wall",
      farmSelect: "All Farms",
      statusFilter: "All Statuses",
      uploadedBy: "Uploaded by",
      aiAnalysis: "AI Analysis",
      farmInfo: "Farm Information"
    },
    // Messages
    messages: {
      title: "Messages",
      typeMessage: "Type your message...",
      loadMore: "Load older messages"
    }
  },
  'zh-CN': {
    nav: {
      dashboard: "仪表板",
      photoWall: "照片墙",
      messages: "消息",
      progress: "任务与行程 (Tasks)",
      healthReport: "健康报告",
      dailySummary: "每日摘要",
      settings: "设置",
      inventory: "库存与收成"
    },
    login: {
      title: "FarmWatch",
      subtitle: "高级农场管理",
      username: "用户名",
      password: "密码",
      loginBtn: "登录",
      loading: "认证中..."
    },
    dashboard: {
      welcome: "欢迎回来",
      totalFarms: "总农场数",
      todayMessages: "今日消息",
      todayPhotos: "今日照片",
      activeTasks: "活跃任务",
      recentActivity: "最近活动",
      recentPhotos: "最近照片",
      quickActions: "快捷操作"
    },
    common: {
      filter: "筛选",
      search: "搜索...",
      all: "全部",
      today: "今天",
      thisWeek: "本周",
      save: "保存",
      cancel: "取消",
      reply: "回复",
      send: "发送",
      logout: "退出登录",
      loading: "加载中...",
      noData: "暂无数据。"
    },
    roles: {
      boss: "老板",
      supervisor: "主管",
      leader: "组长"
    },
    health: {
      healthy: "健康",
      warning: "警告",
      critical: "异常",
      pending: "待分析"
    },
    stages: {
      seeding: "播种",
      fertilizing: "施肥",
      growing: "生长中",
      harvesting: "采收"
    },
    photos: {
      title: "照片墙",
      farmSelect: "所有农场",
      statusFilter: "所有状态",
      uploadedBy: "上传者",
      aiAnalysis: "AI 分析",
      farmInfo: "农场信息"
    },
    messages: {
      title: "消息",
      typeMessage: "输入消息...",
      loadMore: "加载更多历史消息"
    }
  },
  'zh-TW': {
    nav: {
      dashboard: "儀表板",
      photoWall: "照片牆",
      messages: "訊息",
      progress: "任務與行程 (Tasks)",
      healthReport: "健康報告",
      dailySummary: "每日摘要",
      settings: "設定",
      inventory: "庫存與收成"
    },
    login: {
      title: "FarmWatch",
      subtitle: "高級農場管理",
      username: "使用者名稱",
      password: "密碼",
      loginBtn: "登入",
      loading: "認證中..."
    },
    dashboard: {
      welcome: "歡迎回來",
      totalFarms: "總農場數",
      todayMessages: "今日訊息",
      todayPhotos: "今日照片",
      activeTasks: "活躍任務",
      recentActivity: "最近活動",
      recentPhotos: "最近照片",
      quickActions: "快速操作"
    },
    common: {
      filter: "篩選",
      search: "搜尋...",
      all: "全部",
      today: "今天",
      thisWeek: "本週",
      save: "儲存",
      cancel: "取消",
      reply: "回覆",
      send: "發送",
      logout: "登出",
      loading: "載入中...",
      noData: "暫無資料。"
    },
    roles: {
      boss: "老闆",
      supervisor: "主管",
      leader: "組長"
    },
    health: {
      healthy: "健康",
      warning: "警告",
      critical: "異常",
      pending: "待分析"
    },
    stages: {
      seeding: "播種",
      fertilizing: "施肥",
      growing: "生長中",
      harvesting: "採收"
    },
    photos: {
      title: "照片牆",
      farmSelect: "所有農場",
      statusFilter: "所有狀態",
      uploadedBy: "上傳者",
      aiAnalysis: "AI 分析",
      farmInfo: "農場資訊"
    },
    messages: {
      title: "訊息",
      typeMessage: "輸入訊息...",
      loadMore: "載入更多歷史訊息"
    }
  }
};

let currentLang = 'en';
try {
  currentLang = localStorage.getItem('fw_lang') || 'en';
} catch (e) {
  console.warn("localStorage not available", e);
}
if (currentLang === 'zh') currentLang = 'zh-TW'; // migration


export function setLanguage(lang) {
  if (translations[lang]) {
    currentLang = lang;
    localStorage.setItem('fw_lang', lang);
    // Dispatch event so components can re-render
    window.dispatchEvent(new CustomEvent('languagechange', { detail: { lang } }));
  }
}

export function getCurrentLanguage() {
  return currentLang;
}

export function t(key) {
  const keys = key.split('.');
  let value = translations[currentLang];
  
  for (const k of keys) {
    if (value && value[k]) {
      value = value[k];
    } else {
      console.warn(`Missing translation key: ${key}`);
      return key; // Fallback to key
    }
  }
  return value;
}
