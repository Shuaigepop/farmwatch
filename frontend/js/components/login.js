import { t, setLanguage, getCurrentLanguage } from '../i18n.js';
import { auth } from '../auth.js';
import { showToast } from '../api.js';

export function renderLogin(container) {
  const lang = getCurrentLanguage();
  
  container.innerHTML = `
    <div class="login-container">
      <div class="login-bg-elements"></div>
      <button class="lang-toggle" id="lang-btn">${lang === 'en' ? '中文' : 'EN'}</button>
      
      <div class="login-card fade-in" id="login-card">
        <div class="login-header">
          <div class="login-logo">🌿</div>
          <h1 class="login-title">${t('login.title')}</h1>
          <p class="login-subtitle">${t('login.subtitle')}</p>
        </div>
        
        <form id="login-form">
          <div class="form-group">
            <label class="form-label">${t('login.username')}</label>
            <input type="text" class="form-input" id="username" required placeholder="boss / super / leader">
          </div>
          <div class="form-group">
            <label class="form-label">${t('login.password')}</label>
            <input type="password" class="form-input" id="password" required>
          </div>
          <button type="submit" class="btn btn-primary" id="login-btn">
            ${t('login.loginBtn')}
          </button>
        </form>
      </div>
    </div>
  `;

  // Event Listeners
  const langBtn = document.getElementById('lang-btn');
  langBtn.addEventListener('click', () => {
    const newLang = getCurrentLanguage() === 'en' ? 'zh' : 'en';
    setLanguage(newLang);
    renderLogin(container); // Re-render with new language
  });

  const form = document.getElementById('login-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const user = document.getElementById('username').value;
    const pass = document.getElementById('password').value;
    const btn = document.getElementById('login-btn');
    const card = document.getElementById('login-card');

    btn.disabled = true;
    btn.textContent = t('login.loading');
    
    try {
      await auth.login(user, pass);
      window.location.hash = '#/dashboard';
    } catch (err) {
      card.classList.remove('shake');
      void card.offsetWidth; // trigger reflow
      card.classList.add('shake');
      
      btn.disabled = false;
      btn.textContent = t('login.loginBtn');
    }
  });
}
