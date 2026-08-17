import { api } from './api.js';

export const auth = {
  async login(username, password) {
    try {
      const data = await api.auth.login(username, password);
      try {
        localStorage.setItem('fw_token', data.token);
        localStorage.setItem('fw_user', JSON.stringify(data.user));
      } catch(e) {
        console.warn('localStorage not available for login');
      }
      return data.user;
    } catch (error) {
      throw error;
    }
  },

  logout() {
    try {
      localStorage.removeItem('fw_token');
      localStorage.removeItem('fw_user');
    } catch(e) {}
    window.location.hash = '#/login';
  },

  getUser() {
    try {
      const userStr = localStorage.getItem('fw_user');
      if (!userStr) return null;
      return JSON.parse(userStr);
    } catch(e) {
      return null;
    }
  },

  getToken() {
    try {
      return localStorage.getItem('fw_token');
    } catch(e) {
      return null;
    }
  },

  isAuthenticated() {
    try {
      return !!localStorage.getItem('fw_token') && !!this.getUser();
    } catch(e) {
      return false;
    }
  },

  hasRole(role) {
    const user = this.getUser();
    return user && user.role === role;
  },

  canAccessFarm(farmId) {
    const user = this.getUser();
    if (!user) return false;
    if (user.role === 'boss' || user.role === 'supervisor') return true;
    return user.farmId === farmId;
  }
};
