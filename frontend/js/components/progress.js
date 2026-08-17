import { api, showToast } from '../api.js';
import { t } from '../i18n.js';
import { auth } from '../auth.js';

let currentZoneId = '';
let currentViewMode = 'stage'; // 'stage' or 'worker'

export async function renderProgress(container) {
  const user = auth.getUser();
  
  container.innerHTML = `
    <div class="page-container">
      <div class="glass-panel" style="text-align: center; padding: 3rem;">
        <div class="spinner"></div>
      </div>
    </div>
  `;

  try {
    let farmId = user.farmId;
    if (!farmId) {
      const globalFarmSelect = document.getElementById('global-farm-select');
      if (globalFarmSelect && globalFarmSelect.value !== 'all') {
        farmId = parseInt(globalFarmSelect.value);
      }
    }

    const params = {};
    if (farmId) params.farm_id = farmId;
    if (currentZoneId) params.zone_id = currentZoneId;

    const tasks = await api.tasks.list(params);
    let zones = [];
    let users = [];
    
    if (farmId) {
      zones = await api.farms.listZones(farmId);
    }
    
    try {
      if (user.role === 'boss' || user.role === 'supervisor') {
        users = await api.auth.listUsers();
        if (farmId) {
           users = users.filter(u => u.role === 'boss' || u.farm_id === farmId);
        }
      } else {
        users = [{
          id: user.id,
          display_name: user.name,
          role: user.role
        }];
      }
    } catch(err) {
      console.warn("Failed to fetch users", err);
    }

    const userMap = {};
    users.forEach(u => userMap[u.id] = u);

    // Group tasks by stage
    const stages = {
      daily: tasks.filter(t => !t.stage || t.stage === 'daily' || t.stage === 'routine'),
      seeding: tasks.filter(t => t.stage === 'seeding'),
      fertilizing: tasks.filter(t => t.stage === 'fertilizing'),
      growing: tasks.filter(t => t.stage === 'growing'),
      harvesting: tasks.filter(t => t.stage === 'harvesting')
    };

    const renderTaskCard = (task) => {
      let assigneeName = '';
      if (task.assigned_to) {
         assigneeName = userMap[task.assigned_to]?.display_name || 'Worker ' + task.assigned_to;
      }
      return `
      <div class="task-card fade-in">
        <div class="task-header">
          <span class="task-title">${task.title}</span>
          <span class="badge ${task.status === 'completed' ? 'badge-success' : task.status === 'in_progress' ? 'badge-warning' : 'badge-pending'}">${task.status.replace('_', ' ')}</span>
        </div>
        <p class="task-desc">${task.description || ''}</p>
        ${assigneeName ? `<div style="margin-bottom: 0.5rem; font-size: 0.8rem; color: var(--primary);">👤 指派给: ${assigneeName}</div>` : ''}
        <div class="task-footer">
          ${(user.role === 'boss' || user.role === 'supervisor') ? `<button class="icon-btn text-danger delete-task-btn" data-id="${task.id}" style="margin-right: auto; padding: 0;">🗑️</button>` : ''}
          ${task.due_date ? `<span class="badge badge-warning" style="margin-right:0.5rem; font-size:0.75rem;">📅 ${new Date(task.due_date).toLocaleDateString()}</span>` : ''}
          <span class="text-secondary">${new Date(task.updated_at).toLocaleDateString()}</span>
        </div>
      </div>
      `;
    };

    const zoneOptions = zones.map(z => `<option value="${z.id}" ${currentZoneId == z.id ? 'selected' : ''}>${z.parent_zone ? z.parent_zone + ' - ' : ''}${z.name}</option>`).join('');
    const userOptions = users.map(u => `<option value="${u.id}">${u.display_name} (${u.role})</option>`).join('');

    let boardHTML = '';
    if (currentViewMode === 'stage') {
      boardHTML = `
        <div class="kanban-column glass-panel">
          <h3 class="column-title"><span class="stage-icon">🔄</span> 例行工作 (Daily)</h3>
          <div class="kanban-cards">
            ${stages.daily.length ? stages.daily.map(renderTaskCard).join('') : '<p class="empty-state">No tasks</p>'}
          </div>
        </div>
        
        <div class="kanban-column glass-panel">
          <h3 class="column-title"><span class="stage-icon">🌱</span> 播种 (Seeding)</h3>
          <div class="kanban-cards">
            ${stages.seeding.length ? stages.seeding.map(renderTaskCard).join('') : '<p class="empty-state">No tasks</p>'}
          </div>
        </div>
        
        <div class="kanban-column glass-panel">
          <h3 class="column-title"><span class="stage-icon">💧</span> 施肥 (Fertilizing)</h3>
          <div class="kanban-cards">
            ${stages.fertilizing.length ? stages.fertilizing.map(renderTaskCard).join('') : '<p class="empty-state">No tasks</p>'}
          </div>
        </div>

        <div class="kanban-column glass-panel">
          <h3 class="column-title"><span class="stage-icon">🌿</span> 护树 (Growing)</h3>
          <div class="kanban-cards">
            ${stages.growing.length ? stages.growing.map(renderTaskCard).join('') : '<p class="empty-state">No tasks</p>'}
          </div>
        </div>

        <div class="kanban-column glass-panel">
          <h3 class="column-title"><span class="stage-icon">🍎</span> 采收 (Harvesting)</h3>
          <div class="kanban-cards">
            ${stages.harvesting.length ? stages.harvesting.map(renderTaskCard).join('') : '<p class="empty-state">No tasks</p>'}
          </div>
        </div>
      `;
    } else {
      const workerColumns = [];
      const unassigned = tasks.filter(t => !t.assigned_to);
      workerColumns.push({ id: 'unassigned', title: '未指派 (Unassigned)', tasks: unassigned });
      
      users.forEach(u => {
        const assignedTasks = tasks.filter(t => t.assigned_to === u.id);
        workerColumns.push({ id: `user-${u.id}`, title: `👤 ${u.display_name}`, tasks: assignedTasks });
      });

      boardHTML = workerColumns.map(col => `
        <div class="kanban-column glass-panel">
          <h3 class="column-title">${col.title}</h3>
          <div class="kanban-cards">
            ${col.tasks.length ? col.tasks.map(renderTaskCard).join('') : '<p class="empty-state">No scheduled tasks</p>'}
          </div>
        </div>
      `).join('');
    }

    container.innerHTML = `
      <div class="page-container" style="animation: fadeIn 0.4s ease-out;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; flex-wrap: wrap; gap: 1rem;">
          <div>
            <h2 style="display:flex; align-items:center; gap: 1rem;">
              ${t('nav.progress') || 'Progress'}
              <div style="display: flex; background: rgba(0,0,0,0.05); border-radius: 8px; padding: 4px;">
                <button id="view-mode-stage" class="btn ${currentViewMode === 'stage' ? 'btn-primary' : ''}" style="padding: 4px 12px; font-size: 0.9rem; margin: 0; box-shadow: none; border-radius: 6px; ${currentViewMode !== 'stage' ? 'background: transparent; color: var(--text-secondary);' : ''}">按阶段</button>
                <button id="view-mode-worker" class="btn ${currentViewMode === 'worker' ? 'btn-primary' : ''}" style="padding: 4px 12px; font-size: 0.9rem; margin: 0; box-shadow: none; border-radius: 6px; ${currentViewMode !== 'worker' ? 'background: transparent; color: var(--text-secondary);' : ''}">工人行程</button>
              </div>
            </h2>
            <div style="display: flex; gap: 1rem; align-items: center; margin-top: 0.5rem;">
              <select id="zone-filter" class="form-input" style="padding: 0.5rem; border-radius: var(--radius-sm); min-width: 150px;">
                <option value="">全部区域 (All Zones)</option>
                ${zoneOptions}
              </select>
            </div>
          </div>
          ${(user.role === 'boss' || user.role === 'supervisor') && farmId ? `
          <div style="display:flex; gap:0.5rem;">
            <button class="btn btn-success" id="show-plant-btn" style="background:var(--success); color:white;">
              🌱 纪录种植 (Log Planting)
            </button>
            <button class="btn btn-primary" id="show-create-task-btn">
              ➕ 新增任务 (New Task)
            </button>
          </div>
          ` : ''}
        </div>

        <!-- Log Planting Form -->
        <div id="plant-form-container" class="glass-panel" style="display: none; padding: 1.5rem; margin-bottom: 2rem; border: 2px solid var(--success);">
          <h3 style="margin-top: 0; margin-bottom: 1rem; color: var(--success);">🌱 纪录种植 (Log Planting)</h3>
          <p class="text-secondary text-sm" style="margin-bottom:1rem;">系统将自动依照作物的生长天数计算采收期，并产生未来的采收任务。</p>
          <form id="plant-form">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
              <div>
                <label class="text-sm text-secondary">作物种类 (Crop)</label>
                <select id="plant-crop" required class="form-input" style="width: 100%; padding: 0.6rem; border-radius: var(--radius-sm);">
                  <option value="">载入中...</option>
                </select>
              </div>
              <div>
                <label class="text-sm text-secondary">种植区域 (Zone)</label>
                <select id="plant-zone" required class="form-input" style="width: 100%; padding: 0.6rem; border-radius: var(--radius-sm);">
                  <option value="">(选择区域)</option>
                  ${zoneOptions}
                </select>
              </div>
              <div>
                <label class="text-sm text-secondary">种植日期 (Plant Date)</label>
                <input type="date" id="plant-date" required class="form-input" style="width: 100%; padding: 0.6rem; border-radius: var(--radius-sm);">
              </div>
              <div>
                <label class="text-sm text-secondary">备注 (Notes)</label>
                <input type="text" id="plant-notes" placeholder="批次或数量等说明..." class="form-input" style="width: 100%; padding: 0.6rem; border-radius: var(--radius-sm);">
              </div>
            </div>
            <div style="display: flex; gap: 1rem; justify-content: flex-end;">
              <button type="button" class="btn btn-secondary" id="cancel-plant-btn">取消 (Cancel)</button>
              <button type="submit" class="btn btn-success" style="background:var(--success); color:white;">确认种植 (Confirm)</button>
            </div>
          </form>
        </div>

        <div id="create-task-form-container" class="glass-panel" style="display: none; padding: 1.5rem; margin-bottom: 2rem;">
          <h3 style="margin-top: 0; margin-bottom: 1rem;">新增任务 (New Task)</h3>
          <form id="create-task-form">
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
              <div>
                <label class="text-sm text-secondary">标题 (Title)</label>
                <input type="text" id="task-title" required class="form-input" style="width: 100%; padding: 0.6rem; border-radius: var(--radius-sm);">
              </div>
              <div>
                <label class="text-sm text-secondary">阶段 (Stage)</label>
                <select id="task-stage" class="form-input" style="width: 100%; padding: 0.6rem; border-radius: var(--radius-sm);">
                  <option value="seeding">播种 (Seeding)</option>
                  <option value="fertilizing">施肥 (Fertilizing)</option>
                  <option value="growing">生长中 (Growing)</option>
                  <option value="harvesting">采收 (Harvesting)</option>
                </select>
              </div>
              <div>
                <label class="text-sm text-secondary">区域 (Zone)</label>
                <select id="task-zone" class="form-input" style="width: 100%; padding: 0.6rem; border-radius: var(--radius-sm);">
                  <option value="">(不指定区域)</option>
                  ${zoneOptions}
                </select>
              </div>
              <div>
                <label class="text-sm text-secondary">指派给 (Assignee)</label>
                <select id="task-assignee" class="form-input" style="width: 100%; padding: 0.6rem; border-radius: var(--radius-sm);">
                  <option value="">(未指派)</option>
                  ${userOptions}
                </select>
              </div>
              <div>
                <label class="text-sm text-secondary">排程日期 (Due Date)</label>
                <input type="date" id="task-due-date" class="form-input" style="width: 100%; padding: 0.6rem; border-radius: var(--radius-sm);">
              </div>
              <div style="grid-column: 1 / -1;">
                <label class="text-sm text-secondary">详细说明 (Description)</label>
                <input type="text" id="task-desc" class="form-input" style="width: 100%; padding: 0.6rem; border-radius: var(--radius-sm);">
              </div>
            </div>
            <div style="display: flex; gap: 1rem; justify-content: flex-end;">
              <button type="button" class="btn btn-secondary" id="cancel-task-btn">取消 (Cancel)</button>
              <button type="submit" class="btn btn-primary">储存 (Save)</button>
            </div>
          </form>
        </div>

        <div class="kanban-board">
          ${boardHTML}
        </div>
      </div>

      <style>
        .kanban-board {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 1.5rem;
          align-items: start;
        }
        .kanban-column {
          padding: 1.5rem;
          background: rgba(255, 255, 255, 0.4);
          min-height: 400px;
        }
        .column-title {
          font-family: 'Outfit', sans-serif;
          margin: 0 0 1.5rem 0;
          color: var(--primary-dark);
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 1.2rem;
          border-bottom: 2px solid var(--border-color);
          padding-bottom: 0.5rem;
        }
        .stage-icon {
          font-size: 1.5rem;
        }
        .kanban-cards {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        .task-card {
          background: var(--surface);
          border-radius: var(--radius);
          padding: 1rem;
          box-shadow: 0 2px 4px rgba(0,0,0,0.02);
          border: 1px solid var(--border-color);
          transition: transform 0.2s, box-shadow 0.2s;
        }
        .task-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        }
        .task-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 0.5rem;
        }
        .task-title {
          font-weight: 600;
          color: var(--text-primary);
        }
        .task-desc {
          color: var(--text-secondary);
          font-size: 0.9rem;
          margin: 0 0 1rem 0;
          line-height: 1.4;
        }
        .task-footer {
          font-size: 0.8rem;
          display: flex;
          align-items: center;
        }
        .empty-state {
          color: var(--text-secondary);
          text-align: center;
          font-style: italic;
          opacity: 0.7;
          padding: 2rem 0;
        }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .fade-in {
          animation: fadeIn 0.4s ease-out backwards;
        }
      </style>
    `;

    // Filter event
    const zoneFilter = document.getElementById('zone-filter');
    if (zoneFilter) {
      zoneFilter.addEventListener('change', (e) => {
        currentZoneId = e.target.value;
        renderProgress(container);
      });
    }

    // View Mode toggles
    document.getElementById('view-mode-stage')?.addEventListener('click', () => {
       if (currentViewMode !== 'stage') {
          currentViewMode = 'stage';
          renderProgress(container);
       }
    });
    document.getElementById('view-mode-worker')?.addEventListener('click', () => {
       if (currentViewMode !== 'worker') {
          currentViewMode = 'worker';
          renderProgress(container);
       }
    });

    // Toggle Form
    const showBtn = document.getElementById('show-create-task-btn');
    const formContainer = document.getElementById('create-task-form-container');
    const cancelBtn = document.getElementById('cancel-task-btn');
    
    if (showBtn) {
      showBtn.addEventListener('click', () => {
        formContainer.style.display = 'block';
        if (showBtn) showBtn.style.display = 'none';
        if (document.getElementById('show-plant-btn')) document.getElementById('show-plant-btn').style.display = 'none';
      });
    }
    
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        formContainer.style.display = 'none';
        if (showBtn) showBtn.style.display = 'inline-block';
        if (document.getElementById('show-plant-btn')) document.getElementById('show-plant-btn').style.display = 'inline-block';
      });
    }

    // Planting form logic
    const showPlantBtn = document.getElementById('show-plant-btn');
    const plantFormContainer = document.getElementById('plant-form-container');
    const cancelPlantBtn = document.getElementById('cancel-plant-btn');
    const plantForm = document.getElementById('plant-form');
    const cropSelect = document.getElementById('plant-crop');
    
    if (showPlantBtn) {
        showPlantBtn.addEventListener('click', async () => {
            plantFormContainer.style.display = 'block';
            showPlantBtn.style.display = 'none';
            if (showBtn) showBtn.style.display = 'none';
            document.getElementById('plant-date').valueAsDate = new Date(); // default today
            
            // Load crops
            try {
                const crops = await api.farms.listCrops(farmId);
                if (crops.length === 0) {
                    cropSelect.innerHTML = '<option value="">(无设定任何作物，请至设定新增)</option>';
                } else {
                    cropSelect.innerHTML = '<option value="">(选择作物)</option>' + crops.map(c => `<option value="${c.name}">${c.name}</option>`).join('');
                }
            } catch(e) {
                cropSelect.innerHTML = '<option value="">载入失败</option>';
            }
        });
    }
    
    if (cancelPlantBtn) {
        cancelPlantBtn.addEventListener('click', () => {
            plantFormContainer.style.display = 'none';
            if (showPlantBtn) showPlantBtn.style.display = 'inline-block';
            if (showBtn) showBtn.style.display = 'inline-block';
        });
    }
    
    if (plantForm) {
        plantForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = plantForm.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.textContent = 'Processing...';
            
            try {
                const zoneSelect = document.getElementById('plant-zone');
                const zoneName = zoneSelect.options[zoneSelect.selectedIndex].text;
                const payload = {
                    crop_name: document.getElementById('plant-crop').value,
                    planted_date: document.getElementById('plant-date').value,
                    area_or_zone: zoneName,
                    notes: document.getElementById('plant-notes').value
                };
                
                await api.farms.plantCrop(farmId, payload);
                showToast('✅ 成功纪录种植！系统已自动排程未来的采收任务。', 'success');
                plantFormContainer.style.display = 'none';
                if (showPlantBtn) showPlantBtn.style.display = 'inline-block';
                if (showBtn) showBtn.style.display = 'inline-block';
                
                // Optionally reload tasks here if we want to see immediate changes
                renderProgress(container);
            } catch(err) {
                showToast('❌ 纪录失败', 'error');
                btn.disabled = false;
                btn.textContent = '确认种植 (Confirm)';
            }
        });
    }

    // Submit form
    const form = document.getElementById('create-task-form');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = form.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.textContent = 'Saving...';
        
        try {
          const zoneVal = document.getElementById('task-zone').value;
          const assigneeVal = document.getElementById('task-assignee').value;
          const dueDateVal = document.getElementById('task-due-date').value;
          const payload = {
            title: document.getElementById('task-title').value,
            description: document.getElementById('task-desc').value,
            stage: document.getElementById('task-stage').value,
            farm_id: farmId,
            zone_id: zoneVal ? parseInt(zoneVal) : null,
            assigned_to: assigneeVal ? parseInt(assigneeVal) : null,
          };
          if (dueDateVal) {
             payload.due_date = new Date(dueDateVal).toISOString();
          }
          await api.tasks.create(payload);
          showToast('✅ 任务建立成功 (Task Created)', 'success');
          renderProgress(container);
        } catch(err) {
          showToast('❌ 建立失败 (Failed)', 'error');
          btn.disabled = false;
          btn.textContent = '储存 (Save)';
        }
      });
    }
    
    // Delete task
    document.querySelectorAll('.delete-task-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        if (!confirm('确定要删除此任务吗？ (Delete this task?)')) return;
        try {
          await api.tasks.delete(e.currentTarget.dataset.id);
          showToast('✅ 任务已删除 (Task deleted)', 'success');
          renderProgress(container);
        } catch(err) {
          showToast('❌ 删除失败 (Failed)', 'error');
        }
      });
    });

  } catch (err) {
    console.error('Failed to load tasks:', err);
    container.innerHTML = `<div class="page-container"><p style="color:var(--danger)">Error loading progress board.</p></div>`;
  }
}

