import { t, getCurrentLanguage } from '../i18n.js';
import { auth } from '../auth.js';
import { api, apiFetch } from '../api.js';

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
    
    let zonePlans = [];
    let crops = [];
    if (params.farm_id) {
        try {
            zonePlans = await apiFetch(`/farms/${params.farm_id}/zone-plans`);
            crops = await api.farms.listCrops(params.farm_id);
        } catch(e) { console.error("Error loading zone plans", e); }
    }

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

        <!-- FARM PLANNING MAP -->
        <h3 class="section-title" style="margin-bottom: 1rem;">&#x1F33E; 全农场作物规划图 (Farm Planning Map)</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
          ${zonePlans.map(plan => {
             let statusColor = 'var(--text-secondary)';
             let statusText = '空置 (Idle)';
             let countdown = '';
             let emoji = '&#x26AA;';
             
             if (plan.status === 'planted' || plan.status === 'growing') {
                 statusColor = 'var(--primary)';
                 statusText = '生长中 (Growing)';
                 emoji = '&#x1F33F;';
                 if (plan.days_left !== null) {
                     if (plan.days_left <= 0) {
                         statusColor = 'var(--warning)';
                         countdown = '<br><span style="color:var(--warning);font-weight:bold;">&#x26A0;&#xFE0F; 今日可采收</span>';
                     } else if (plan.days_left <= 3) {
                         statusColor = 'var(--warning)';
                         countdown = \`<br><span style="color:var(--warning);font-weight:bold;">&#x26A0;&#xFE0F; \${plan.days_left} 天后采收</span>\`;
                     } else {
                         countdown = \`<br><span class="text-secondary">剩余 \${plan.days_left} 天</span>\`;
                     }
                 }
             } else if (plan.status === 'harvesting') {
                 statusColor = '#d97706';
                 statusText = '采收期 (Harvesting)';
                 emoji = '&#x1F34E;';
             } else if (plan.status === 'preparing') {
                 statusColor = '#8b5cf6';
                 statusText = '翻土重种 (Preparing)';
                 emoji = '&#x1F6A7;';
             }
             
             const parentStr = plan.parent_zone ? \`\${plan.parent_zone} - \` : '';
             
             return \`
             <div class="glass-panel" style="padding: 1rem; cursor: pointer; border-left: 4px solid \${statusColor};" onclick="openZonePlanModal(\${plan.id})">
                 <div class="flex justify-between items-center">
                     <h4 style="margin: 0; font-size: 1.1rem;">\${parentStr}\${plan.zone_name}</h4>
                     <span style="font-size: 1.2rem;">\${emoji}</span>
                 </div>
                 <div style="margin-top: 0.5rem; font-size: 0.95rem;">
                     <strong>\${plan.crop_name || '未种植'}</strong>
                     <div style="color: \${statusColor}; margin-top: 0.2rem;">\${statusText}\${countdown}</div>
                 </div>
                 \${plan.next_crop_name ? \`<div style="margin-top: 0.5rem; font-size: 0.8rem;" class="text-secondary">▶ 下一轮: \${plan.next_crop_name}</div>\` : ''}
             </div>
             \`;
          }).join('')}
          \${zonePlans.length === 0 ? '<p class="text-secondary">没有规划数据。请先建立区域。</p>' : ''}
        </div>

        <!-- ZONE PLAN MODAL CONTAINER -->
        <div id="zone-plan-modal" class="modal-overlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; justify-content:center; align-items:center;">
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
    
      // Inject Modal logic globally
      window.openZonePlanModal = (planId) => {
          const plan = zonePlans.find(p => p.id === planId);
          if (!plan) return;
          
          const cropOptions = crops.map(c => \`<option value="\${c.id}" \${plan.crop_id === c.id ? 'selected' : ''}>\${c.name}</option>\`).join('');
          
          const modalHtml = \`
            <div class="glass-panel" style="background: var(--bg-primary); padding: 2rem; width: 90%; max-width: 500px; max-height: 90vh; overflow-y: auto; box-shadow: 0 10px 25px rgba(0,0,0,0.2);">
                <div class="flex justify-between items-center" style="margin-bottom: 1.5rem;">
                    <h3 style="margin:0;">\${plan.parent_zone ? plan.parent_zone + ' - ' : ''}\${plan.zone_name} 规划详情</h3>
                    <button class="icon-btn" onclick="document.getElementById('zone-plan-modal').style.display='none'">❌</button>
                </div>
                
                <div class="form-group">
                    <label>状态 (Status)</label>
                    <select id="zp-status" class="form-control">
                        <option value="idle" \${plan.status === 'idle' ? 'selected' : ''}>空置 (Idle)</option>
                        <option value="planted" \${plan.status === 'planted' || plan.status === 'growing' ? 'selected' : ''}>生长中 (Planted/Growing)</option>
                        <option value="harvesting" \${plan.status === 'harvesting' ? 'selected' : ''}>采收期 (Harvesting)</option>
                        <option value="preparing" \${plan.status === 'preparing' ? 'selected' : ''}>翻土重种 (Preparing)</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>当前作物 (Current Crop)</label>
                    <select id="zp-crop" class="form-control">
                        <option value="">-- 选择作物 --</option>
                        \${cropOptions}
                    </select>
                </div>
                
                <div class="form-group">
                    <label>种植日期 (Planted Date)</label>
                    <input type="date" id="zp-date" class="form-control" value="\${plan.planted_date || ''}">
                </div>
                
                <div class="form-group">
                    <label>下一轮轮作 (Next Crop)</label>
                    <input type="text" id="zp-next" class="form-control" value="\${plan.next_crop_name || ''}" placeholder="例如: 黄瓜">
                </div>
                
                <div class="form-group">
                    <label>历史采收记录 (Last Harvest kg)</label>
                    <input type="number" step="0.1" id="zp-kg" class="form-control" value="\${plan.last_harvest_kg || ''}">
                </div>
                
                <div style="margin-top: 2rem; display: flex; gap: 1rem;">
                    <button class="btn btn-primary" style="flex:1;" onclick="saveZonePlan(\${plan.id})">保存设定 (Save)</button>
                    \${plan.status === 'growing' ? \`<button class="btn btn-warning" style="flex:1;" onclick="actionZonePlan(\${plan.id}, 'harvest')">▶ 开始采收</button>\` : ''}
                    \${plan.status === 'harvesting' ? \`<button class="btn btn-secondary" style="flex:1; background:#8b5cf6;" onclick="actionZonePlan(\${plan.id}, 'finish')">▶ 采收结束 (去翻土)</button>\` : ''}
                    \${plan.status === 'preparing' ? \`<button class="btn btn-danger" style="flex:1;" onclick="actionZonePlan(\${plan.id}, 'clear')">▶ 清空区域</button>\` : ''}
                </div>
            </div>
          \`;
          
          const modal = document.getElementById('zone-plan-modal');
          modal.innerHTML = modalHtml;
          modal.style.display = 'flex';
      };
      
      window.saveZonePlan = async (planId) => {
          const status = document.getElementById('zp-status').value;
          const cropId = document.getElementById('zp-crop').value;
          const plantedDate = document.getElementById('zp-date').value;
          const nextCrop = document.getElementById('zp-next').value;
          const kg = document.getElementById('zp-kg').value;
          
          if (status === 'idle') {
              await actionZonePlan(planId, 'clear');
              return;
          }
          
          if (!cropId || !plantedDate) {
              alert("必须选择作物和种植日期");
              return;
          }
          
          try {
              // Create or replace crop plan
              await apiFetch(\`/farms/\${params.farm_id}/zone-plans\`, {
                  method: 'POST',
                  headers: {'Content-Type': 'application/json'},
                  body: JSON.stringify({
                      zone_id: zonePlans.find(p => p.id === planId).zone_id,
                      crop_id: parseInt(cropId),
                      planted_date: plantedDate
                  })
              });
              
              // Update extra info
              await apiFetch(\`/farms/zone-plans/\${planId}\`, {
                  method: 'PUT',
                  headers: {'Content-Type': 'application/json'},
                  body: JSON.stringify({
                      status: status,
                      next_crop_name: nextCrop || null,
                      last_harvest_kg: kg ? parseFloat(kg) : null
                  })
              });
              
              document.getElementById('zone-plan-modal').style.display = 'none';
              renderDashboard(container); // reload
          } catch(e) {
              alert("保存失败");
          }
      };
      
      window.actionZonePlan = async (planId, action) => {
          try {
              await apiFetch(\`/farms/zone-plans/\${planId}/action/\${action}\`, { method: 'POST' });
              document.getElementById('zone-plan-modal').style.display = 'none';
              renderDashboard(container); // reload
          } catch(e) {
              alert("操作失败");
          }
      };
      
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
