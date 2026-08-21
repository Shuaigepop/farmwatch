import { t, getCurrentLanguage } from '../i18n.js';
import { auth } from '../auth.js';
import { api, apiFetch } from '../api.js';

function buildCropOption(c, selectedId) {
  var sel = (selectedId === c.id) ? ' selected' : '';
  return '<option value="' + c.id + '"' + sel + '>' + c.name + '</option>';
}

function buildStatusOption(value, label, currentStatus) {
  var match = false;
  if (value === 'planted') {
    match = (currentStatus === 'planted' || currentStatus === 'growing');
  } else {
    match = (currentStatus === value);
  }
  var sel = match ? ' selected' : '';
  return '<option value="' + value + '"' + sel + '>' + label + '</option>';
}

function buildActionButtons(plan) {
  var html = '';
  if (plan.status === 'growing') {
    html += '<button class="btn btn-warning" style="flex:1;" onclick="actionZonePlan(' + plan.id + ', \'harvest\')">&#x25B6; Start Harvest</button>';
  }
  if (plan.status === 'harvesting') {
    html += '<button class="btn btn-secondary" style="flex:1; background:#8b5cf6;" onclick="actionZonePlan(' + plan.id + ', \'finish\')">&#x25B6; End Harvest</button>';
  }
  if (plan.status === 'preparing') {
    html += '<button class="btn btn-danger" style="flex:1;" onclick="actionZonePlan(' + plan.id + ', \'clear\')">&#x25B6; Clear Zone</button>';
  }
  return html;
}

function buildModalHtml(plan, cropOptionsHtml) {
  var titlePrefix = plan.parent_zone ? (plan.parent_zone + ' - ') : '';
  var nextVal = plan.next_crop_name || '';
  var kgVal = plan.last_harvest_kg || '';
  var dateVal = plan.planted_date || '';

  var html = '<div class="glass-panel" style="background: var(--bg-primary); padding: 2rem; width: 90%; max-width: 500px; max-height: 90vh; overflow-y: auto; box-shadow: 0 10px 25px rgba(0,0,0,0.2);">';
  html += '<div class="flex justify-between items-center" style="margin-bottom: 1.5rem;">';
  html += '<h3 style="margin:0;">' + titlePrefix + plan.zone_name + ' Details</h3>';
  html += '<button class="icon-btn" onclick="document.getElementById(\'zone-plan-modal\').style.display=\'none\'">&#x274C;</button>';
  html += '</div>';

  html += '<div class="form-group">';
  html += '<label>Status</label>';
  html += '<select id="zp-status" class="form-control">';
  html += buildStatusOption('idle', 'Idle', plan.status);
  html += buildStatusOption('planted', 'Growing', plan.status);
  html += buildStatusOption('harvesting', 'Harvesting', plan.status);
  html += buildStatusOption('preparing', 'Preparing', plan.status);
  html += '</select></div>';

  html += '<div class="form-group">';
  html += '<label>Current Crop</label>';
  html += '<select id="zp-crop" class="form-control">';
  html += '<option value="">-- Select Crop --</option>';
  html += cropOptionsHtml;
  html += '</select></div>';

  html += '<div class="form-group">';
  html += '<label>Planted Date</label>';
  html += '<input type="date" id="zp-date" class="form-control" value="' + dateVal + '">';
  html += '</div>';

  html += '<div class="form-group">';
  html += '<label>Next Crop</label>';
  html += '<input type="text" id="zp-next" class="form-control" value="' + nextVal + '" placeholder="e.g. Cucumber">';
  html += '</div>';

  html += '<div class="form-group">';
  html += '<label>Last Harvest (kg)</label>';
  html += '<input type="number" step="0.1" id="zp-kg" class="form-control" value="' + kgVal + '">';
  html += '</div>';

  html += '<div style="margin-top: 2rem; display: flex; gap: 1rem;">';
  html += '<button class="btn btn-primary" style="flex:1;" onclick="saveZonePlan(' + plan.id + ')">Save</button>';
  html += buildActionButtons(plan);
  html += '</div>';

  html += '</div>';
  return html;
}

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
            zonePlans = await apiFetch('/farms/' + params.farm_id + '/zone-plans');
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
          
          <h3 class="section-title" style="margin-bottom: 1rem;">All Farms</h3>
          <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem;">
            ${farms.map(farm => {
              const fMessages = messages.filter(m => m.farm_id === farm.id);
              const fPhotos = photos.filter(p => p.farm_id === farm.id);
              return `
              <div class="glass-panel farm-card" data-farm-id="${farm.id}" style="padding: 1.5rem; cursor: pointer; transition: transform 0.2s;">
                <h4 style="font-size: 1.25rem; margin-bottom: 0.5rem; color: var(--primary);">${farm.name}</h4>
                <p class="text-secondary text-sm" style="margin-bottom: 1rem;">&#x1F4CD; ${farm.location || 'N/A'}</p>
                <div class="flex justify-between text-sm">
                  <span>&#x1F4AC; ${fMessages.length} ${t('nav.messages') || 'Messages'}</span>
                  <span>&#x1F4F8; ${fPhotos.length} ${t('nav.photoWall') || 'Photos'}</span>
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
      // Build zone plan cards HTML
      var zonePlanCardsHtml = '';
      zonePlans.forEach(function(plan) {
          var statusColor = 'var(--text-secondary)';
          var statusText = 'Idle';
          var countdown = '';
          var emoji = '&#x26AA;';

          if (plan.status === 'planted' || plan.status === 'growing') {
              statusColor = 'var(--primary)';
              statusText = 'Growing';
              emoji = '&#x1F33F;';
              if (plan.days_left !== null) {
                  if (plan.days_left <= 0) {
                      statusColor = 'var(--warning)';
                      countdown = '<br><span style="color:var(--warning);font-weight:bold;">&#x26A0;&#xFE0F; Ready to harvest!</span>';
                  } else if (plan.days_left <= 3) {
                      statusColor = 'var(--warning)';
                      countdown = '<br><span style="color:var(--warning);font-weight:bold;">&#x26A0;&#xFE0F; ' + plan.days_left + ' days to harvest</span>';
                  } else {
                      countdown = '<br><span class="text-secondary">' + plan.days_left + ' days left</span>';
                  }
              }
          } else if (plan.status === 'harvesting') {
              statusColor = '#d97706';
              statusText = 'Harvesting';
              emoji = '&#x1F34E;';
          } else if (plan.status === 'preparing') {
              statusColor = '#8b5cf6';
              statusText = 'Preparing';
              emoji = '&#x1F6A7;';
          }

          var parentStr = plan.parent_zone ? (plan.parent_zone + ' - ') : '';
          var nextCropHtml = '';
          if (plan.next_crop_name) {
              nextCropHtml = '<div style="margin-top: 0.5rem; font-size: 0.8rem;" class="text-secondary">&#x25B6; Next: ' + plan.next_crop_name + '</div>';
          }

          zonePlanCardsHtml += '<div class="glass-panel" style="padding: 1rem; cursor: pointer; border-left: 4px solid ' + statusColor + ';" onclick="openZonePlanModal(' + plan.id + ')">';
          zonePlanCardsHtml += '<div class="flex justify-between items-center">';
          zonePlanCardsHtml += '<h4 style="margin: 0; font-size: 1.1rem;">' + parentStr + plan.zone_name + '</h4>';
          zonePlanCardsHtml += '<span style="font-size: 1.2rem;">' + emoji + '</span>';
          zonePlanCardsHtml += '</div>';
          zonePlanCardsHtml += '<div style="margin-top: 0.5rem; font-size: 0.95rem;">';
          zonePlanCardsHtml += '<strong>' + (plan.crop_name || 'Not planted') + '</strong>';
          zonePlanCardsHtml += '<div style="color: ' + statusColor + '; margin-top: 0.2rem;">' + statusText + countdown + '</div>';
          zonePlanCardsHtml += '</div>';
          zonePlanCardsHtml += nextCropHtml;
          zonePlanCardsHtml += '</div>';
      });

      if (zonePlans.length === 0) {
          zonePlanCardsHtml = '<p class="text-secondary">No planning data. Please create zones first.</p>';
      }

      // Build recent messages HTML
      var recentMsgHtml = '';
      if (recentMessages.length) {
          recentMessages.forEach(function(msg) {
              var borderColor = msg.is_reply ? 'var(--primary)' : 'var(--warning)';
              var bgColor = msg.is_reply ? 'rgba(45,80,22,0.05)' : 'rgba(245,127,23,0.05)';
              var userName = msg.line_user_name || 'System';
              var farmName = farmMap[msg.farm_id] || 'Unknown Farm';
              var content = msg.message_type === 'image' ? '[Photo]' : (msg.content || '[Empty]');
              recentMsgHtml += '<div style="padding: 1rem; border-left: 3px solid ' + borderColor + '; background: ' + bgColor + '; border-radius: 0 var(--radius-md) var(--radius-md) 0;">';
              recentMsgHtml += '<div class="flex justify-between">';
              recentMsgHtml += '<strong>' + userName + ' (' + farmName + ')</strong>';
              recentMsgHtml += '<span class="text-secondary text-sm">' + getTimeAgo(msg.created_at) + '</span>';
              recentMsgHtml += '</div>';
              recentMsgHtml += '<p class="text-sm" style="margin-top: 0.5rem;">' + content + '</p>';
              recentMsgHtml += '</div>';
          });
      } else {
          recentMsgHtml = '<p class="text-secondary">' + t('common.noData') + '</p>';
      }

      // Build recent photos HTML
      var recentPhotoHtml = '';
      if (recentPhotos.length) {
          recentPhotos.forEach(function(p) {
              recentPhotoHtml += '<img src="' + p.thumbnail_path + '" style="width:100%; height:100px; object-fit:cover; border-radius:var(--radius-sm);" alt="farm">';
          });
      } else {
          recentPhotoHtml = '<p class="text-secondary">' + t('common.noData') + '</p>';
      }

      container.innerHTML = `
        <div class="page-container" style="animation: fadeIn 0.4s ease-out;">
          <div class="flex justify-between items-center" style="margin-bottom: 2rem;">
            <div>
              <h2>${t('dashboard.welcome')}, ${user.name}</h2>
              <p class="text-secondary">${dateStr}</p>
            </div>
          </div>

        <!-- FARM PLANNING MAP -->
        <h3 class="section-title" style="margin-bottom: 1rem;">&#x1F33E; Farm Planning Map</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; margin-bottom: 2rem;">
          ${zonePlanCardsHtml}
        </div>

        <!-- ZONE PLAN MODAL CONTAINER -->
        <div id="zone-plan-modal" class="modal-overlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:9999; justify-content:center; align-items:center;">
        </div>

        <div class="stats-grid slide-in">
          <div class="stat-card">
            <div class="stat-icon stat-green">&#x1F33E;</div>
            <div class="stat-info">
              <div class="stat-value">${farms.length}</div>
              <div class="stat-label">${t('dashboard.totalFarms')}</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-blue">&#x1F4AC;</div>
            <div class="stat-info">
              <div class="stat-value">${todayMessages}</div>
              <div class="stat-label">${t('dashboard.todayMessages')}</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-amber">&#x1F4F8;</div>
            <div class="stat-info">
              <div class="stat-value">${todayPhotos}</div>
              <div class="stat-label">${t('dashboard.todayPhotos')}</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon stat-purple">&#x1F4CB;</div>
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
              ${recentMsgHtml}
            </div>
          </div>

          <div class="glass-panel" style="flex: 1; padding: 1.5rem; min-width: 300px;">
            <h3 class="section-title">${t('dashboard.recentPhotos')}</h3>
            <div class="photo-grid" style="grid-template-columns: repeat(2, 1fr); gap: 0.5rem;">
              ${recentPhotoHtml}
            </div>
          </div>
        </div>
        </div>
      </div>
    `;
    
      // Inject Modal logic globally
      window.openZonePlanModal = function(planId) {
          var plan = zonePlans.find(function(p) { return p.id === planId; });
          if (!plan) return;
          
          var cropOptionsHtml = crops.map(function(c) { return buildCropOption(c, plan.crop_id); }).join('');
          var modalHtml = buildModalHtml(plan, cropOptionsHtml);
          
          var modal = document.getElementById('zone-plan-modal');
          modal.innerHTML = modalHtml;
          modal.style.display = 'flex';
      };
      
      window.saveZonePlan = async function(planId) {
          var status = document.getElementById('zp-status').value;
          var cropId = document.getElementById('zp-crop').value;
          var plantedDate = document.getElementById('zp-date').value;
          var nextCrop = document.getElementById('zp-next').value;
          var kg = document.getElementById('zp-kg').value;
          
          if (status === 'idle') {
              await actionZonePlan(planId, 'clear');
              return;
          }
          
          if (!cropId || !plantedDate) {
              alert("Please select a crop and planting date");
              return;
          }
          
          try {
              // Create or replace crop plan
              await apiFetch('/farms/' + params.farm_id + '/zone-plans', {
                  method: 'POST',
                  headers: {'Content-Type': 'application/json'},
                  body: JSON.stringify({
                      zone_id: zonePlans.find(function(p) { return p.id === planId; }).zone_id,
                      crop_id: parseInt(cropId),
                      planted_date: plantedDate
                  })
              });
              
              // Update extra info
              await apiFetch('/farms/zone-plans/' + planId, {
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
              alert("Save failed");
          }
      };
      
      window.actionZonePlan = async function(planId, action) {
          try {
              await apiFetch('/farms/zone-plans/' + planId + '/action/' + action, { method: 'POST' });
              document.getElementById('zone-plan-modal').style.display = 'none';
              renderDashboard(container); // reload
          } catch(e) {
              alert("Action failed");
          }
      };
      
    }
  } catch (err) {
    console.error('Failed to load dashboard data:', err);
    container.innerHTML = '<div class="page-container"><p style="color:var(--danger)">Error loading dashboard data.</p></div>';
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
  if (diffMins < 60) return diffMins + ' mins ago';
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return diffHours + ' hours ago';
  const diffDays = Math.floor(diffHours / 24);
  return diffDays + ' days ago';
}
