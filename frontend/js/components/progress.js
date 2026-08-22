import { api, showToast } from '../api.js';
import { t } from '../i18n.js';
import { auth } from '../auth.js';

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

    if (!farmId) {
       container.innerHTML = `<div class="page-container"><div class="glass-panel text-center">Please select a farm from the sidebar first.</div></div>`;
       return;
    }

    // Fetch farm data
    const farms = await api.farms.list();
    const currentFarm = farms.find(f => f.id === farmId);
    
    // Fetch users for assignment
    let users = [];
    try {
      if (user.role === 'boss' || user.role === 'supervisor') {
        users = await api.auth.listUsers();
        users = users.filter(u => u.role === 'boss' || u.farm_id === farmId);
      } else {
        users = [{ id: user.id, display_name: user.name, role: user.role }];
      }
    } catch(err) {}
    const userMap = {};
    users.forEach(u => userMap[u.id] = u);
    const userOptions = users.map(u => `<option value="${u.id}">${u.display_name} (${u.role})</option>`).join('');

    // Fetch zones
    const zones = await api.farms.listZones(farmId);
    const zoneOptions = zones.map(z => `<option value="${z.id}">${z.parent_zone ? z.parent_zone + ' - ' : ''}${z.name}</option>`).join('');

    // Fetch tasks
    const tasks = await api.tasks.list({ farm_id: farmId });
    
    // Filter tasks for today's tracker
    const today = new Date().toLocaleDateString();
    const todayTasks = tasks.filter(t => {
      // If due_date is today or earlier and not completed, or completed today
      const isCompletedToday = t.status === 'completed' && new Date(t.updated_at).toLocaleDateString() === today;
      const isPending = t.status !== 'completed';
      return isPending || isCompletedToday;
    });

    const pendingTasks = todayTasks.filter(t => t.status !== 'completed');
    const completedTasks = todayTasks.filter(t => t.status === 'completed');

    const renderTaskCard = (task) => {
      let assigneeName = task.assigned_to ? (userMap[task.assigned_to]?.display_name || 'Worker') : '未指派';
      return `
      <div class="task-card fade-in">
        <div class="task-header" style="display:flex; justify-content:space-between; align-items:center;">
          <label style="display:flex; align-items:center; gap:0.5rem; cursor:pointer; font-weight:600;">
            <input type="checkbox" class="task-checkbox" data-id="${task.id}" ${task.status === 'completed' ? 'checked disabled' : ''}>
            <span style="${task.status === 'completed' ? 'text-decoration:line-through; color:var(--text-secondary);' : ''}">${task.title}</span>
          </label>
          <span class="badge ${task.status === 'completed' ? 'badge-success' : 'badge-warning'}">${task.status === 'completed' ? '已完成' : '待办'}</span>
        </div>
        <p class="text-secondary text-sm" style="margin-left: 1.5rem; margin-top:0.2rem; margin-bottom:0.5rem;">${task.description || ''}</p>
        <div style="margin-left: 1.5rem; display:flex; justify-content:space-between; align-items:center; font-size:0.8rem;">
           <span style="color:var(--primary);">👤 ${assigneeName}</span>
           ${(user.role === 'boss' || user.role === 'supervisor') ? `<button class="icon-btn delete-task-btn text-danger" data-id="${task.id}" style="padding:0;">🗑️ 删除</button>` : ''}
        </div>
      </div>
      `;
    };

    container.innerHTML = `
      <div class="page-container slide-in">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem;">
          <div>
            <h2>Task Dashboard (任务总管)</h2>
            <p class="text-secondary">Farm: ${currentFarm?.name || 'Unknown'}</p>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin-bottom: 2rem;">
          
          <!-- Farm Settings Control Panel -->
          ${(user.role === 'boss' || user.role === 'supervisor') ? `
          <div class="glass-panel" style="padding: 1.5rem; border-top: 4px solid var(--primary);">
            <h3 style="margin-top:0; color:var(--primary); display:flex; align-items:center; gap:0.5rem;">⚙️ 发送时间设定 (Time Settings)</h3>
            <p class="text-secondary text-sm" style="margin-bottom:1rem;">设定机器人自动检查工作与发送总结的时间。</p>
            <form id="time-settings-form">
              <div style="display:grid; gap:1rem; margin-bottom:1rem;">
                <div>
                  <label class="text-sm font-bold">每日催收/检查时间 (Missing Work Check)</label>
                  <input type="time" id="farm-check-time" class="form-input" value="${currentFarm?.check_time || '18:00'}" style="width:100%; padding:0.5rem; border-radius:var(--radius-sm);">
                </div>
                <div>
                  <label class="text-sm font-bold">每日工作总结推播 (Daily Summary)</label>
                  <input type="time" id="farm-summary-time" class="form-input" value="${currentFarm?.summary_time || '19:00'}" style="width:100%; padding:0.5rem; border-radius:var(--radius-sm);">
                </div>
              </div>
              <button type="submit" class="btn btn-primary" style="width:100%;">储存时间设定 (Save Times)</button>
            </form>
          </div>
          ` : ''}

          <!-- Add Ad-hoc Task -->
          ${(user.role === 'boss' || user.role === 'supervisor') ? `
          <div class="glass-panel" style="padding: 1.5rem; border-top: 4px solid var(--success);">
            <h3 style="margin-top:0; color:var(--success); display:flex; align-items:center; gap:0.5rem;">➕ 新增临时任务 (New Ad-hoc Task)</h3>
            <form id="create-task-form">
              <div style="display:grid; gap:0.5rem; margin-bottom:1rem;">
                <input type="text" id="task-title" required placeholder="任务标题 (Task Title)" class="form-input" style="padding:0.5rem; border-radius:var(--radius-sm);">
                <input type="text" id="task-desc" placeholder="详细说明 (Description)" class="form-input" style="padding:0.5rem; border-radius:var(--radius-sm);">
                <div style="display:flex; gap:0.5rem;">
                   <select id="task-assignee" class="form-input" style="flex:1; padding:0.5rem; border-radius:var(--radius-sm);">
                     <option value="">(指派给所有人 / All)</option>
                     ${userOptions}
                   </select>
                   <select id="task-zone" class="form-input" style="flex:1; padding:0.5rem; border-radius:var(--radius-sm);">
                     <option value="">(不限区域)</option>
                     ${zoneOptions}
                   </select>
                </div>
              </div>
              <button type="submit" class="btn btn-success" style="width:100%; background:var(--success); color:white;">建立任务 (Create Task)</button>
            </form>
          </div>
          ` : ''}
        </div>

        <!-- Today's Tracking Board -->
        <h3 style="margin-bottom: 1rem; padding-bottom:0.5rem; border-bottom:2px solid var(--border-color);">🎯 今日工作追踪 (Today's Tracker)</h3>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem; margin-bottom: 2rem;">
           <div class="glass-panel" style="padding: 1.5rem; background:rgba(255,255,255,0.4);">
             <h4 style="margin-top:0; color:var(--primary-dark);">待办事项 (To-Do) - ${pendingTasks.length}</h4>
             <div style="display:flex; flex-direction:column; gap:0.8rem; margin-top:1rem;">
               ${pendingTasks.length ? pendingTasks.map(renderTaskCard).join('') : '<p class="text-secondary text-center text-sm">目前没有待办工作</p>'}
             </div>
           </div>
           
           <div class="glass-panel" style="padding: 1.5rem; background:rgba(255,255,255,0.4);">
             <h4 style="margin-top:0; color:var(--success);">已完成 (Done) - ${completedTasks.length}</h4>
             <div style="display:flex; flex-direction:column; gap:0.8rem; margin-top:1rem;">
               ${completedTasks.length ? completedTasks.map(renderTaskCard).join('') : '<p class="text-secondary text-center text-sm">尚未有完成的工作</p>'}
             </div>
           </div>
        </div>

        <!-- SOP Management Section -->
        ${(user.role === 'boss' || user.role === 'supervisor') ? `
        <h3 style="margin-bottom: 1rem; padding-bottom:0.5rem; border-bottom:2px solid var(--border-color);">📅 例行工作设定 (SOP Management)</h3>
        <div class="glass-panel" style="padding: 1.5rem;">
          <p class="text-secondary text-sm" style="margin-bottom: 1rem;">定义每日例行公事。系统每天会自动将这些工作加到当天的待办清单中。</p>
          <div id="sop-list-container" style="max-height: 300px; overflow-y: auto; margin-bottom: 1rem;">
            <div class="text-center text-sm">载入中...</div>
          </div>
          <div style="padding: 1rem; border-top: 2px solid var(--primary); background: rgba(45,80,22,0.05); border-radius: var(--radius-md);">
            <h4 style="margin-top:0; margin-bottom: 0.8rem; color: var(--primary);">➕ 新增例行工作 (Add SOP)</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
              <input type="text" id="new-sop-title" placeholder="工作标题 (如: 巡视果园)" class="form-input" style="padding: 0.5rem; border-radius: var(--radius-sm);">
              <select id="new-sop-role" class="form-input" style="padding: 0.5rem; border-radius: var(--radius-sm);">
                <option value="worker">指派给：员工 (Worker)</option>
                <option value="foreman">指派给：工头 (Foreman)</option>
              </select>
            </div>
            <input type="text" id="new-sop-desc" placeholder="详细说明" class="form-input" style="width:100%; padding: 0.5rem; border-radius: var(--radius-sm); margin-bottom:0.5rem;">
            <button class="btn btn-primary" id="add-sop-btn" style="width: 100%;">新增例行工作 (Add SOP)</button>
          </div>
        </div>
        ` : ''}
      </div>

      <style>
        .task-card {
          background: var(--surface);
          border-radius: var(--radius-sm);
          padding: 1rem;
          box-shadow: 0 2px 4px rgba(0,0,0,0.02);
          border: 1px solid var(--border-color);
        }
        .task-checkbox {
          width: 18px;
          height: 18px;
          cursor: pointer;
        }
      </style>
    `;

    // Handle Time Settings
    const timeForm = document.getElementById('time-settings-form');
    if (timeForm) {
      timeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const check_time = document.getElementById('farm-check-time').value;
        const summary_time = document.getElementById('farm-summary-time').value;
        const btn = timeForm.querySelector('button');
        btn.disabled = true;
        btn.textContent = '储存中...';
        try {
          await api.farms.update(farmId, { ...currentFarm, check_time, summary_time });
          showToast('✅ 时间设定已更新！', 'success');
        } catch(err) {
          showToast('❌ 更新失败', 'error');
        } finally {
          btn.disabled = false;
          btn.textContent = '储存时间设定 (Save Times)';
        }
      });
    }

    // Handle Task Creation
    const taskForm = document.getElementById('create-task-form');
    if (taskForm) {
      taskForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = taskForm.querySelector('button');
        btn.disabled = true;
        try {
          const payload = {
            farm_id: farmId,
            title: document.getElementById('task-title').value,
            description: document.getElementById('task-desc').value,
            stage: 'routine',
            zone_id: document.getElementById('task-zone').value || null,
            assigned_to: document.getElementById('task-assignee').value || null,
            status: 'pending'
          };
          await api.tasks.create(payload);
          showToast('✅ 任务新增成功', 'success');
          renderProgress(container); // reload
        } catch(err) {
          showToast('❌ 新增失败', 'error');
          btn.disabled = false;
        }
      });
    }

    // Handle Task Checkbox (Mark Completed)
    document.querySelectorAll('.task-checkbox').forEach(box => {
      box.addEventListener('change', async (e) => {
        const taskId = e.target.dataset.id;
        const isChecked = e.target.checked;
        if (isChecked) {
          try {
            await api.tasks.update(taskId, { status: 'completed' });
            renderProgress(container);
          } catch(err) {
             showToast('❌ 更新失败', 'error');
             e.target.checked = false;
          }
        }
      });
    });

    // Handle Task Deletion
    document.querySelectorAll('.delete-task-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        if(!confirm('确定删除此任务？')) return;
        try {
          await api.tasks.delete(e.target.dataset.id);
          renderProgress(container);
        } catch(err) {
          showToast('❌ 删除失败', 'error');
        }
      });
    });

    // Load SOPs
    if (user.role === 'boss' || user.role === 'supervisor') {
      const sopContainer = document.getElementById('sop-list-container');
      const loadSOPs = async () => {
        try {
          const token = localStorage.getItem('fw_token');
          const resp = await fetch('/api/tasks/recurring?farm_id=' + farmId, {
            headers: { 'Authorization': 'Bearer ' + token }
          });
          const sops = await resp.json();
          if (!sops.length) {
            sopContainer.innerHTML = '<div class="text-secondary text-center text-sm" style="padding:1rem;">目前没有设定的例行工作</div>';
            return;
          }
          sopContainer.innerHTML = sops.map(s => `
            <div style="padding: 1rem; border-bottom: 1px solid var(--border-color); display:flex; justify-content:space-between; align-items:center;">
              <div>
                <div style="font-weight:600;">\${s.title} <span class="badge badge-info" style="font-size:0.7rem;">\${s.target_role === 'foreman' ? '工头任务' : '员工任务'}</span></div>
                <div class="text-secondary text-sm">\${s.description || ''}</div>
              </div>
              <button class="icon-btn text-danger delete-sop-btn" data-id="\${s.id}">🗑️</button>
            </div>
          `).join('');

          document.querySelectorAll('.delete-sop-btn').forEach(btn => {
            btn.addEventListener('click', async (e) => {
              if(!confirm('确定删除？')) return;
              try {
                await fetch('/api/tasks/recurring/' + e.target.dataset.id, {
                  method: 'DELETE',
                  headers: { 'Authorization': 'Bearer ' + token }
                });
                loadSOPs();
              } catch(err) { showToast('❌ 删除失败', 'error'); }
            });
          });
        } catch(err) {
          sopContainer.innerHTML = '<div class="text-danger">载入失败</div>';
        }
      };
      
      await loadSOPs();

      const addSopBtn = document.getElementById('add-sop-btn');
      if (addSopBtn) {
        addSopBtn.addEventListener('click', async () => {
          const title = document.getElementById('new-sop-title').value;
          const desc = document.getElementById('new-sop-desc').value;
          const role = document.getElementById('new-sop-role').value;
          if(!title) return showToast('请输入标题', 'error');
          addSopBtn.disabled = true;
          try {
            const token = localStorage.getItem('fw_token');
            await fetch('/api/tasks/recurring', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
              body: JSON.stringify({
                farm_id: farmId, title, description: desc || title, target_role: role,
                cron_expression: '0 6 * * *', is_active: true
              })
            });
            document.getElementById('new-sop-title').value = '';
            document.getElementById('new-sop-desc').value = '';
            loadSOPs();
          } catch(err) { showToast('❌ 新增失败', 'error'); }
          addSopBtn.disabled = false;
        });
      }
    }

  } catch (err) {
    console.error('Failed to load tasks:', err);
    container.innerHTML = \`<div class="page-container"><p style="color:var(--danger)">Error loading progress board.</p></div>\`;
  }
}
