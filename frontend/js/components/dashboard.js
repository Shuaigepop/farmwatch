import { t, getCurrentLanguage } from '../i18n.js';
import { auth } from '../auth.js';
import { api } from '../api.js';

export async function renderDashboard(container) {
  const user = auth.getUser();
  const dateStr = new Intl.DateTimeFormat(getCurrentLanguage(), { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }).format(new Date());

  // Show loading state initially
  container.innerHTML = `
    <div class="page-container">
      <div class="flex justify-between items-center" style="margin-bottom: 2rem;">
        <div>
          <h2>${t('dashboard.welcome')}, ${user.name}</h2>
          <p class="text-secondary">${dateStr}</p>
        </div>
      </div>
      <div class="glass-panel" style="text-align: center; padding: 3rem;">
        <div class="spinner"></div>
      </div>
    </div>
  `;

  try {
    const params = {};
    if (user.farmId) params.farm_id = user.farmId;
    else {
      const globalFarmSelect = document.getElementById('global-farm-select');
      if (globalFarmSelect && globalFarmSelect.value !== 'all') {
        params.farm_id = parseInt(globalFarmSelect.value);
      }
    }

    // Fetch dynamic data
    const farms = await api.farms.list();
    const farmMap = {};
    farms.forEach(f => farmMap[f.id] = f.name);
    
    const messages = await api.messages.list(params);
    const photos = await api.photos.list(params);
    const tasks = await api.tasks.list(params);

    // Calculate stats
    const today = new Date().toISOString().split('T')[0];
    const todayMessages = messages.filter(m => m.created_at.startsWith(today)).length;
    const todayPhotos = photos.filter(p => p.captured_at.startsWith(today)).length;
    const activeTasks = tasks.filter(t => t.status === 'in_progress').length;
    
    // Sort for recent activity
    const recentMessages = messages.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 5);
    const recentPhotos = photos.sort((a, b) => new Date(b.captured_at) - new Date(a.captured_at)).slice(0, 4);

    const isAllFarms = !params.farm_id;

    if (isAllFarms) {
      // CARD VIEW FOR ALL FARMS
      container.innerHTML = `
        <div class="page-container" style="animation: fadeIn 0.4s ease-out;">
          <div class="flex justify-between items-center" style="margin-bottom: 2rem;">
            <div>
              <h2>${t('dashboard.welcome')}, ${user.name}</h2>
              <p class="text-secondary">${dateStr}</p>
            </div>
          </div>
          
          <h3 class="section-title" style="margin-bottom: 1rem;">所有农场 (All Farms)</h3>
          <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem;">
            ${farms.map(farm => {
              const fMessages = messages.filter(m => m.farm_id === farm.id);
              const fPhotos = photos.filter(p => p.farm_id === farm.id);
              return `
              <div class="glass-panel farm-card" data-farm-id="${farm.id}" style="padding: 1.5rem; cursor: pointer; transition: transform 0.2s;">
                <h4 style="font-size: 1.25rem; margin-bottom: 0.5rem; color: var(--primary);">${farm.name}</h4>
                <p class="text-secondary text-sm" style="margin-bottom: 1rem;">📍 ${farm.location || '未设定'}</p>
                <div class="flex justify-between text-sm">
                  <span>💬 ${fMessages.length} ${t('nav.messages') || '讯息'}</span>
                  <span>📸 ${fPhotos.length} ${t('nav.photoWall') || '照片'}</span>
                </div>
              </div>
              `;
            }).join('')}
          </div>
        </div>
      `;

      // Add click listener to cards
      container.querySelectorAll('.farm-card').forEach(card => {
        card.addEventListener('click', () => {
          const fid = card.dataset.farmId;
          const select = document.getElementById('global-farm-select');
          if (select) {
            select.value = fid;
            localStorage.setItem('fw_selected_farm', fid);
            window.dispatchEvent(new CustomEvent('farmchange', { detail: { farmId: fid } }));
          }
        });
      });
      
      // Add hover effect via JS since CSS isn't updated
      container.querySelectorAll('.farm-card').forEach(card => {
        card.addEventListener('mouseenter', () => card.style.transform = 'translateY(-5px)');
        card.addEventListener('mouseleave', () => card.style.transform = 'translateY(0)');
      });

    } else {
      // DETAIL VIEW FOR SINGLE FARM
      container.innerHTML = `
        <div class="page-container" style="animation: fadeIn 0.4s ease-out;">
          <div class="flex justify-between items-center" style="margin-bottom: 2rem;">
            <div>
              <h2>${t('dashboard.welcome')}, ${user.name}</h2>
              <p class="text-secondary">${dateStr}</p>
            </div>
          </div>


        <div class="stats-grid slide-in">
          <div class="stat-card">
            <div class="stat-icon stat-green">🌾</div>
            <div class="stat-info">
              <div class="stat-value">${farms.length}</div>
              <div class="stat-label">${t('dashboard.totalFarms')}</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-blue">💬</div>
            <div class="stat-info">
              <div class="stat-value">${todayMessages}</div>
              <div class="stat-label">${t('dashboard.todayMessages')}</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-amber">📸</div>
            <div class="stat-info">
              <div class="stat-value">${todayPhotos}</div>
              <div class="stat-label">${t('dashboard.todayPhotos')}</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-purple">📋</div>
            <div class="stat-info">
              <div class="stat-value">${activeTasks}</div>
              <div class="stat-label">${t('dashboard.activeTasks')}</div>
            </div>
          </div>
        </div>

        <div class="flex gap-4" style="flex-wrap: wrap;">
          <div class="glass-panel" style="flex: 2; padding: 1.5rem; min-width: 300px;">
            <h3 class="section-title">${t('dashboard.recentActivity')}</h3>
            <div class="flex flex-col gap-4">
              ${recentMessages.length ? recentMessages.map(msg => `
                <div style="padding: 1rem; border-left: 3px solid ${msg.is_reply ? 'var(--primary)' : 'var(--warning)'}; background: ${msg.is_reply ? 'rgba(45,80,22,0.05)' : 'rgba(245,127,23,0.05)'}; border-radius: 0 var(--radius-md) var(--radius-md) 0;">
                  <div class="flex justify-between">
                    <strong>${msg.line_user_name || 'System'} (${farmMap[msg.farm_id] || 'Unknown Farm'})</strong>
                    <span class="text-secondary text-sm" title="${new Date(msg.created_at).toLocaleString()}">${getTimeAgo(msg.created_at)}</span>
                  </div>
                  <p class="text-sm" style="margin-top: 0.5rem;">${msg.message_type === 'image' ? '[Photo]' : (msg.content || '[Empty]')}</p>
                </div>
              `).join('') : `<p class="text-secondary">${t('common.noData')}</p>`}
            </div>
          </div>

          <div class="glass-panel" style="flex: 1; padding: 1.5rem; min-width: 300px;">
            <h3 class="section-title">${t('dashboard.recentPhotos')}</h3>
            <div class="photo-grid" style="grid-template-columns: repeat(2, 1fr); gap: 0.5rem;">
              ${recentPhotos.length ? recentPhotos.map(p => `
                <img src="${p.thumbnail_path}" style="width:100%; height:100px; object-fit:cover; border-radius:var(--radius-sm);" alt="farm">
              `).join('') : `<p class="text-secondary">${t('common.noData')}</p>`}
            </div>
          </div>
        </div>
        </div>
      </div>
    `;
    }
  } catch (err) {
    console.error('Failed to load dashboard data:', err);
    container.innerHTML = `<div class="page-container"><p style="color:var(--danger)">Error loading dashboard data.</p></div>`;
  }
}

function getCurrentLocale() {
  const lang = localStorage.getItem('fw_lang') || 'en';
  return lang === 'zh' ? 'zh-CN' : 'en-US';
}

function getTimeAgo(dateString) {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now - date;
  const diffMins = Math.round(diffMs / 60000);
  
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins} mins ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} hours ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} days ago`;
}
