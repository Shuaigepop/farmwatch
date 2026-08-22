import { t } from '../i18n.js';
import { auth } from '../auth.js';
import { api } from '../api.js';

export async function renderSidebar(container, currentRoute) {
  const user = auth.getUser();
  if (!user) return;

  const roleLabels = {
    boss: t('roles.boss'),
    supervisor: t('roles.supervisor'),
    leader: t('roles.leader')
  };

  const navItems = [
    { id: 'dashboard', icon: '📊', label: t('nav.dashboard'), route: 'index.html#/dashboard' }
  ];

  if ((user.role || '').toLowerCase() === 'boss') {
    navItems.push({ id: 'settings', icon: '⚙️', label: t('nav.settings'), route: 'index.html#/settings' });
  }

    navItems.push(
      { id: 'photos', icon: '🖼️', label: t('nav.photoWall'), route: 'index.html#/photos' },
      { id: 'messages', icon: '💬', label: t('nav.messages'), route: 'index.html#/messages' },
      { id: 'progress', icon: '📋', label: 'Task Dashboard (任务总管)', route: 'index.html#/progress' },
      { id: 'health', icon: '🩺', label: t('nav.healthReport'), route: 'index.html#/health' },
      { id: 'summary', icon: '📄', label: t('nav.dailySummary') || 'Daily Summary', route: 'index.html#/summary' },
      { id: 'inventory', icon: '📦', label: t('nav.inventory') || 'Inventory (资材设定)', route: 'index.html#/inventory' },
      { id: 'deliveries', icon: '🧾', label: 'Deliveries (出货对账)', route: 'index.html#/deliveries' }
    );

  let farmSelectorHtml = '';
  if (['boss', 'supervisor'].includes((user.role || '').toLowerCase())) {
    let farms = [];
    try {
      farms = await api.farms.list();
    } catch(e) {}
    
    farmSelectorHtml = `
      <div class="farm-selector">
        <select class="farm-select" id="global-farm-select">
          <option value="all">${t('common.all')} Farms</option>
          ${farms.map(f => `<option value="${f.id}">${f.name}</option>`).join('')}
        </select>
      </div>
    `;
  }

  container.innerHTML = `
    <div class="sidebar" id="sidebar">
      <div class="sidebar-header">
        <div class="sidebar-brand">🌿 FarmWatch</div>
      </div>
      
      <div class="user-profile">
        <div class="avatar">${user.name.charAt(0)}</div>
        <div class="user-info">
          <div class="user-name">${user.name}</div>
          <div class="user-role">${roleLabels[(user.role || '').toLowerCase()]}</div>
        </div>
      </div>
      
      ${farmSelectorHtml}
      
      <nav class="nav-menu">
        ${navItems.map(item => `
          <a href="${item.disabled ? 'javascript:void(0)' : item.route}" 
             class="nav-item ${currentRoute.endsWith(item.route.replace('index.html', '')) || currentRoute === item.route ? 'active' : ''} ${item.disabled ? 'disabled' : ''}">
            <span class="nav-icon">${item.icon}</span>
            <span>${item.label}</span>
          </a>
        `).join('')}
      </nav>
    </div>
  `;

  // Attach event listener to close sidebar on mobile when nav item clicked
  const sidebar = document.getElementById('sidebar');
  if (sidebar) {
    sidebar.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', () => {
        if (window.innerWidth <= 768) {
          sidebar.classList.remove('open');
        }
      });
    });
  }

  // Handle farm selection change
  const farmSelect = document.getElementById('global-farm-select');
  if (farmSelect) {
    // Restore previous selection if it exists in localStorage
    const savedFarmId = localStorage.getItem('fw_selected_farm') || 'all';
    if (farmSelect.querySelector(`option[value="${savedFarmId}"]`)) {
      farmSelect.value = savedFarmId;
    }

    farmSelect.addEventListener('change', (e) => {
      localStorage.setItem('fw_selected_farm', e.target.value);
      // Dispatch event to notify components to reload
      window.dispatchEvent(new CustomEvent('farmchange', { detail: { farmId: e.target.value } }));
    });
  }
}
