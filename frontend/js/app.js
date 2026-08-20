import { auth } from './auth.js?v=14';
import { setLanguage, getCurrentLanguage, t } from './i18n.js?v=14';
import { renderLogin } from './components/login.js?v=14';
import { renderSidebar } from './components/sidebar.js?v=14';
import { renderDashboard } from './components/dashboard.js?v=14';
import { renderPhotoWall } from './components/photo-wall.js?v=14';
import { renderMessages } from './components/message-feed.js?v=14';
import { renderHealthReport } from './components/health-report.js?v=14';
import { renderProgress } from './components/progress.js?v=14';
import { renderDailySummary } from './components/daily-summary.js?v=14';
import { renderSettings } from './components/settings.js?v=14';
import { renderInventory } from './components/inventory.js?v=14';
import { renderDeliveries } from './components/deliveries.js?v=14';
import { renderScheduler } from './components/scheduler.js?v=14';
const appContainer = document.getElementById('app');

// App Shell (Sidebar + Header + Main Content)
function renderAppShell() {
  appContainer.innerHTML = `
    <div id="sidebar-container"></div>
    <div class="main-content">
      <header class="top-header">
        <div class="header-left">
          <button class="menu-toggle" id="mobile-menu-btn">☰</button>
          <div id="breadcrumb" class="font-semibold text-secondary"></div>
        </div>
        <div class="header-right">
          <button class="lang-toggle" style="position:static;" id="header-lang-btn">
            ${getCurrentLanguage() === 'zh-TW' ? '繁中' : (getCurrentLanguage() === 'zh-CN' ? '简中' : 'EN')}
          </button>
          <button class="icon-btn">🔔</button>
          <button class="icon-btn" id="logout-btn" title="Logout">🚪</button>
        </div>
      </header>
      <main id="main-view" style="flex: 1; overflow-y: auto; background: var(--bg-color);"></main>
    </div>
  `;

  // Attach shell events
  document.getElementById('logout-btn').addEventListener('click', () => {
    auth.logout();
  });

  const langBtn = document.getElementById('header-lang-btn');
  langBtn.addEventListener('click', () => {
    const current = getCurrentLanguage();
    let newLang = 'zh-TW';
    if (current === 'en') newLang = 'zh-TW';
    else if (current === 'zh-TW') newLang = 'zh-CN';
    else if (current === 'zh-CN') newLang = 'en';
    
    setLanguage(newLang);
  });

  document.getElementById('mobile-menu-btn').addEventListener('click', () => {
    const sidebar = document.querySelector('.sidebar');
    if (sidebar) sidebar.classList.toggle('open');
  });

  // Re-render current view when farm changes
  window.addEventListener('farmchange', () => {
    handleRoute();
  });
}

// Router
async function handleRoute() {
  const hash = window.location.hash || '#/dashboard';
  
  // Close sidebar on mobile if open
  const sidebar = document.querySelector('.sidebar');
  if (sidebar && sidebar.classList.contains('open')) {
    sidebar.classList.remove('open');
  }
  
  // Auth Guard
  if (!auth.isAuthenticated() && hash !== '#/login') {
    window.location.hash = '#/login';
    return;
  }
  
  if (auth.isAuthenticated() && hash === '#/login') {
    window.location.hash = '#/dashboard';
    return;
  }

  // Handle Login Route explicitly
  if (hash === '#/login') {
    renderLogin(appContainer);
    return;
  }

  // Ensure App Shell exists
  if (!document.getElementById('main-view')) {
    renderAppShell();
  }

  // Update Sidebar
  const sidebarContainer = document.getElementById('sidebar-container');
  if (sidebarContainer) {
    await renderSidebar(sidebarContainer, hash);
  }

  // Render View
  const mainView = document.getElementById('main-view');
  const breadcrumb = document.getElementById('breadcrumb');
  
  mainView.innerHTML = ''; // Clear previous view

  try {
    switch (hash) {
      case '#/dashboard':
        breadcrumb.textContent = t('nav.dashboard');
        await renderDashboard(mainView);
        break;
      case '#/photos':
        breadcrumb.textContent = t('nav.photoWall');
        await renderPhotoWall(mainView);
        break;
      case '#/messages':
        breadcrumb.textContent = t('nav.messages');
        await renderMessages(mainView);
        break;
      case '#/progress':
        breadcrumb.textContent = t('nav.progress');
        await renderProgress(mainView);
        break;
      case '#/health':
        breadcrumb.textContent = t('nav.healthReport');
        await renderHealthReport(mainView);
        break;
      case '#/summary':
        breadcrumb.textContent = t('nav.dailySummary');
        await renderDailySummary(mainView);
        break;
      case '#/settings':
        breadcrumb.textContent = t('nav.settings');
        await renderSettings(mainView);
        break;
      case '#/deliveries':
        breadcrumb.textContent = 'Deliveries (出货对账)';
        await renderDeliveries(mainView);
        break;
      case '#/inventory':
        breadcrumb.textContent = t('nav.inventory') || 'Inventory';
        await renderInventory(mainView);
        break;
      case '#/scheduler':
        breadcrumb.textContent = 'Scheduler (AI派发)';
        await renderScheduler(mainView);
        break;
      default:
        mainView.innerHTML = `<div class="page-container"><h2>404 Not Found</h2></div>`;
    }
  } catch (err) {
    console.error("View Render Error:", err);
    mainView.innerHTML = `<div class="page-container"><h2 style="color:var(--danger)">Error loading page</h2><p>${err.message}</p></div>`;
  }
}

// Global Event Listeners
window.addEventListener('hashchange', handleRoute);
window.addEventListener('languagechange', () => {
  renderAppShell();
  handleRoute();
});

// Initialize
function init() {
  handleRoute();
}

// Start app
init();
