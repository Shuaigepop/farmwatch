import { t } from '../i18n.js';
import { auth } from '../auth.js';
import { api, showToast } from '../api.js';

export async function renderSettings(container) {
  const user = auth.getUser();
  if ((user.role || '').toLowerCase() !== 'boss') {
    container.innerHTML = `<div class="page-container"><h3>Unauthorized</h3><p>Only Boss can access settings.</p></div>`;
    return;
  }

  container.innerHTML = `
    <div class="page-container slide-in">
      <div style="margin-bottom: 2rem;">
        <h2>${t('nav.settings') || 'Settings'}</h2>
        <p class="text-secondary">Manage your farms and system settings.</p>
      </div>
      
      <div style="display: flex; flex-wrap: wrap; gap: 2rem;">
        <!-- Left: Create Form -->
        <div class="glass-panel" style="padding: 2rem; flex: 1; min-width: 300px;">
        <h3 class="section-title">新增农场 (Create New Farm)</h3>
        <p class="text-secondary text-sm" style="margin-bottom: 1.5rem;">
          LINE 群组如果与此处设定的农场名称完全相同，系统将自动绑定讯息。
        </p>
        <form id="create-farm-form" class="flex flex-col gap-4">
          <div class="form-group">
            <label>农场名称 (Farm Name)</label>
            <input type="text" id="farm-name" required placeholder="例如：阳光山农场" class="form-input" style="width: 100%; padding: 0.8rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
          <div class="form-group">
            <label>所在区域 (Location)</label>
            <input type="text" id="farm-location" placeholder="例如：北区" class="form-input" style="width: 100%; padding: 0.8rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
          <div class="form-group">
            <label>备注描述 (Description)</label>
            <textarea id="farm-desc" placeholder="请输入相关说明..." class="form-input" rows="3" style="width: 100%; padding: 0.8rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);"></textarea>
          </div>
          <button type="submit" class="btn btn-primary" id="create-farm-btn" style="padding: 0.8rem; background: var(--primary); color: white; border: none; border-radius: var(--radius-sm); cursor: pointer;">
            建立农场 (Create)
          </button>
        </form>
        </div>
        
        <!-- Right: Farm List -->
        <div class="glass-panel" style="padding: 2rem; flex: 1; min-width: 300px;">
          <h3 class="section-title">现有农场 (Existing Farms)</h3>
          <div id="farm-list-container" style="margin-top: 1rem; max-height: 400px; overflow-y: auto;">
            <div class="skeleton" style="height: 100px; width: 100%;"></div>
          </div>
        </div>
      </div>
      
      <div style="display: flex; flex-wrap: wrap; gap: 2rem; margin-top: 2rem;">
        <!-- User Management -->
        <div class="glass-panel" style="padding: 2rem; flex: 1; min-width: 300px;">
          <h3 class="section-title">使用者管理 (User Management)</h3>
          <div id="user-list-container" style="margin-top: 1rem; max-height: 400px; overflow-y: auto;">
            <div class="skeleton" style="height: 100px; width: 100%;"></div>
          </div>
        </div>
        
        <!-- LINE Integration -->
        <div class="glass-panel" style="padding: 2rem; flex: 1; min-width: 300px;">
          <h3 class="section-title">LINE 群组连结 (LINE Groups)</h3>
          <p class="text-secondary text-sm" style="margin-bottom: 1rem;">管理已加入的 LINE 群组与农场的连结，重新连结后机器人会自动推播通知。</p>
          <div id="line-groups-container" style="margin-top: 1rem; max-height: 400px; overflow-y: auto;">
            <div class="skeleton" style="height: 100px; width: 100%;"></div>
          </div>
        </div>
      </div>
      
      <div style="display: flex; flex-wrap: wrap; gap: 2rem; margin-top: 2rem;">
        <!-- Zone Management -->
        <div class="glass-panel" style="padding: 2rem; flex: 1; min-width: 300px;">
          <h3 class="section-title">区域管理 (Zone Management)</h3>
          <p class="text-secondary text-sm" style="margin-bottom: 1rem;">管理农场底下的区域 (例如: A区、A1等)</p>
          
          <div class="form-group" style="margin-bottom: 1rem;">
            <select id="zone-farm-select" class="form-input" style="width: 100%; padding: 0.8rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
              <option value="">载入中 (Loading)...</option>
            </select>
          </div>
          
          <div id="zone-list-container" style="margin-top: 1rem; max-height: 300px; overflow-y: auto; border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 0.5rem; background: rgba(255,255,255,0.3);">
            <div class="text-secondary text-sm text-center" style="padding: 1rem;">请先选择上方的农场</div>
          </div>
          
          <div style="padding: 1.2rem; border-top: 2px solid var(--primary); margin-top: 1rem; background: rgba(45,80,22,0.05); border-radius: 0 0 var(--radius-md) var(--radius-md);">
            <h4 style="margin-bottom: 0.8rem; color: var(--primary);">➕ 新增区域 (Add Zone)</h4>
            <div style="display: flex; gap: 0.5rem; margin-bottom: 0.5rem;">
              <input type="text" id="new-zone-parent" placeholder="主区域 (选填, 如: A区)" class="form-input" style="flex: 1; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
              <input type="text" id="new-zone-name" placeholder="子区域 (必填, 如: A1)" required class="form-input" style="flex: 1; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
            </div>
            <button class="btn btn-primary" id="add-zone-btn" style="width: 100%; padding: 0.6rem; background: var(--primary); color: white; border: none; border-radius: var(--radius-sm); cursor: pointer;" disabled>
              新增区域 (Create Zone)
            </button>
          </div>
        </div>
      </div>

      <div style="display: flex; flex-wrap: wrap; gap: 2rem; margin-top: 2rem;">
        <!-- Crop Management -->
        <div class="glass-panel" style="padding: 2rem; flex: 1; min-width: 300px;">
          <h3 class="section-title">作物设定 (Crop Management)</h3>
          <p class="text-secondary text-sm" style="margin-bottom: 1rem;">管理作物生长周期与采收时间。当您在任务建立「种植」时，将自动参考这些天数。</p>
          
          <div class="form-group" style="margin-bottom: 1rem;">
            <select id="crop-farm-select" class="form-input" style="width: 100%; padding: 0.8rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
              <option value="">载入中 (Loading)...</option>
            </select>
          </div>
          
          <div id="crop-list-container" style="margin-top: 1rem; max-height: 350px; overflow-y: auto; border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 0.5rem; background: rgba(255,255,255,0.3);">
            <div class="text-secondary text-sm text-center" style="padding: 1rem;">请先选择上方的农场</div>
          </div>
          
          <div style="padding: 1.2rem; border-top: 2px solid var(--primary); margin-top: 1rem; background: rgba(45,80,22,0.05); border-radius: 0 0 var(--radius-md) var(--radius-md);">
            <h4 style="margin-bottom: 0.8rem; color: var(--primary);">➕ 新增作物 (Add Crop)</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
              <div>
                  <label class="text-secondary text-sm">作物名称</label>
                  <input type="text" id="new-crop-name" placeholder="(如: Bendi)" required class="form-input" style="width:100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
              </div>
              <div>
                  <label class="text-secondary text-sm">生长天数</label>
                  <input type="number" id="new-crop-grow" placeholder="几天后开始采收" value="0" class="form-input" style="width:100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
              </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
              <div>
                  <label class="text-secondary text-sm">连续采收期 (天)</label>
                  <input type="number" id="new-crop-duration" placeholder="可连续采收几天" value="1" class="form-input" style="width:100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
              </div>
              <div>
                  <label class="text-secondary text-sm" style="display:block;">多年生植物</label>
                  <label style="display:flex; align-items:center; gap:0.5rem; height: 35px;"><input type="checkbox" id="new-crop-perennial"> (打勾代表不下架)</label>
              </div>
            </div>
            <button class="btn btn-primary" id="add-crop-btn" style="width: 100%; padding: 0.6rem; background: var(--primary); color: white; border: none; border-radius: var(--radius-sm); cursor: pointer;" disabled>
              新增作物 (Create Crop)
            </button>
          </div>
        </div>
      </div>

      <div style="display: flex; flex-wrap: wrap; gap: 2rem; margin-top: 2rem;">
        <div class="glass-panel" style="padding: 2rem; flex: 1; min-width: 300px;">
          <h3 class="section-title">SOP / Daily Tasks Management</h3>
          <p class="text-secondary text-sm" style="margin-bottom: 1rem;">Define recurring daily tasks for workers and foremen. These will automatically appear in the AI scheduler.</p>
          
          <div class="form-group" style="margin-bottom: 1rem;">
            <select id="sop-farm-select" class="form-input" style="width: 100%; padding: 0.8rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
              <option value="">Loading...</option>
            </select>
          </div>
          
          <div id="sop-list-container" style="margin-top: 1rem; max-height: 350px; overflow-y: auto; border: 1px solid var(--border-color); border-radius: var(--radius-sm); padding: 0.5rem; background: rgba(255,255,255,0.3);">
            <div class="text-secondary text-sm text-center" style="padding: 1rem;">Select a farm above</div>
          </div>
          
          <div style="padding: 1.2rem; border-top: 2px solid var(--primary); margin-top: 1rem; background: rgba(45,80,22,0.05); border-radius: 0 0 var(--radius-md) var(--radius-md);">
            <h4 style="margin-bottom: 0.8rem; color: var(--primary);">&#x2795; Add New SOP Task</h4>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
              <div>
                <label class="text-secondary text-sm">Task Title</label>
                <input type="text" id="new-sop-title" placeholder="e.g. Morning watering" class="form-input" style="width:100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
              </div>
              <div>
                <label class="text-secondary text-sm">Assign To</label>
                <select id="new-sop-role" class="form-input" style="width:100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
                  <option value="worker">Worker</option>
                  <option value="foreman">Foreman</option>
                </select>
              </div>
            </div>
            <div class="form-group" style="margin-bottom: 0.5rem;">
              <label class="text-secondary text-sm">Description</label>
              <input type="text" id="new-sop-desc" placeholder="Detailed instructions" class="form-input" style="width:100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
            </div>
            <button class="btn btn-primary" id="add-sop-btn" style="width: 100%; padding: 0.6rem; background: var(--primary); color: white; border: none; border-radius: var(--radius-sm); cursor: pointer;" disabled>
              Add SOP Task
            </button>
          </div>
        </div>
      </div>
    </div>
  `;

  await loadFarmList();
  await loadUserList();
  await loadLineGroups();
  await initZoneManagement();
  await initCropManagement();
  await initSOPManagement();

  document.getElementById('create-farm-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('create-farm-btn');
    const name = document.getElementById('farm-name').value;
    const location = document.getElementById('farm-location').value;
    const description = document.getElementById('farm-desc').value;

    btn.disabled = true;
    btn.textContent = '建立中 (Creating)...';

    try {
      await api.farms.create({ name, location, description });
      showToast('✅ 农场建立成功！(Farm created successfully)', 'success');
      document.getElementById('create-farm-form').reset();
      await loadFarmList(); // Refresh list
    } catch (err) {
      showToast('❌ 建立失败 (Failed to create farm)', 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = '建立农场 (Create)';
    }
  });
}

async function loadFarmList() {
  const container = document.getElementById('farm-list-container');
  if (!container) return;
  
  try {
    const farms = await api.farms.list();
    if (!farms || farms.length === 0) {
      container.innerHTML = `<p class="text-secondary text-sm">目前没有任何农场。</p>`;
      return;
    }
    
    container.innerHTML = farms.map(farm => `
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 1rem; border-bottom: 1px solid var(--border-color);">
        <div>
          <div style="font-weight: 600;">${farm.name}</div>
          <div class="text-secondary text-sm">${farm.location || '未定区域'}</div>
        </div>
        <button class="icon-btn delete-farm-btn" data-id="${farm.id}" style="color: var(--danger);" title="删除农场">🗑️</button>
      </div>
    `).join('');
    
    // Add delete event listeners
    document.querySelectorAll('.delete-farm-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const farmId = e.currentTarget.dataset.id;
        if (confirm('确定要删除这个农场吗？此操作无法撤销。')) {
          try {
            await api.farms.delete(farmId);
            showToast('✅ 农场已删除', 'success');
            await loadFarmList(); // Refresh list
            await loadLineGroups(); // Also refresh dropdowns
          } catch(err) {
            showToast('❌ 删除失败', 'error');
          }
        }
      });
    });
  } catch (e) {
    container.innerHTML = `<p style="color: var(--danger)">无法载入农场列表</p>`;
  }
}

async function loadUserList() {
  const container = document.getElementById('user-list-container');
  if (!container) return;
  
  try {
    const users = await api.auth.listUsers();
    const farms = await api.farms.list();
    if (!users || users.length === 0) {
      container.innerHTML = `<p class="text-secondary text-sm">目前没有任何使用者。</p>`;
      return;
    }
    
    const farmOptions = farms.map(f => `<option value="${f.id}">${f.name}</option>`).join('');
    
    let html = users.map(u => `
      <div style="padding: 1rem; border-bottom: 1px solid var(--border-color);" id="user-card-${u.id}">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.8rem;">
          <span class="badge badge-info">${u.role}</span>
          ${users.length > 1 ? `<button class="icon-btn delete-user-btn" data-id="${u.id}" data-name="${u.display_name}" style="color: var(--danger); font-size: 1.2rem;" title="删除此使用者">🗑️</button>` : ''}
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
          <div>
            <label class="text-secondary text-sm">显示名称</label>
            <input type="text" id="uname-${u.id}" value="${u.display_name}" class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
          <div>
            <label class="text-secondary text-sm">登入帐号</label>
            <input type="text" id="ulogin-${u.id}" value="${u.username}" class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
          <div>
            <label class="text-secondary text-sm">新密码 (留空不改)</label>
            <input type="password" id="upw-${u.id}" placeholder="输入新密码..." class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
          <div>
            <label class="text-secondary text-sm">角色</label>
            <select id="urole-${u.id}" class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
              <option value="boss" ${u.role === 'boss' ? 'selected' : ''}>老板 (Boss)</option>
              <option value="supervisor" ${u.role === 'supervisor' ? 'selected' : ''}>主管 (Supervisor)</option>
              <option value="leader" ${u.role === 'leader' ? 'selected' : ''}>組長 (Leader)</option>
            </select>
          </div>
        </div>
        <button class="btn btn-secondary save-user-btn" data-id="${u.id}" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); cursor: pointer; margin-top: 0.3rem;">
          💾 储存变更 (Save)
        </button>
      </div>
    `).join('');
    
    // Add New User form
    html += `
      <div style="padding: 1.2rem; border-top: 2px solid var(--primary); margin-top: 0.5rem; background: rgba(45,80,22,0.05); border-radius: 0 0 var(--radius-md) var(--radius-md);">
        <h4 style="margin-bottom: 0.8rem; color: var(--primary);">➕ 新增使用者 (Add New User)</h4>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
          <div>
            <label class="text-secondary text-sm">显示名称</label>
            <input type="text" id="new-user-name" placeholder="例如：张三" class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
          <div>
            <label class="text-secondary text-sm">登入帐号</label>
            <input type="text" id="new-user-login" placeholder="例如：zhangsan" class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 0.5rem;">
          <div>
            <label class="text-secondary text-sm">密码</label>
            <input type="password" id="new-user-pw" placeholder="设定密码" class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
          </div>
          <div>
            <label class="text-secondary text-sm">角色</label>
            <select id="new-user-role" class="form-input" style="width: 100%; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
              <option value="leader">組長 (Leader)</option>
              <option value="supervisor">主管 (Supervisor)</option>
              <option value="boss">老板 (Boss)</option>
            </select>
          </div>
        </div>
        <button class="btn btn-primary" id="add-user-btn" style="width: 100%; padding: 0.6rem; background: var(--primary); color: white; border: none; border-radius: var(--radius-sm); cursor: pointer;">
          新增使用者 (Create User)
        </button>
      </div>
    `;
    
    container.innerHTML = html;
    
    // Save user changes
    document.querySelectorAll('.save-user-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const userId = e.currentTarget.dataset.id;
        const displayName = document.getElementById(`uname-${userId}`).value.trim();
        const username = document.getElementById(`ulogin-${userId}`).value.trim();
        const newPw = document.getElementById(`upw-${userId}`).value;
        const role = document.getElementById(`urole-${userId}`).value;
        
        if (!displayName || !username) {
          showToast('❌ 名称和帐号不能为空', 'error');
          return;
        }
        
        btn.disabled = true;
        btn.textContent = '储存中...';
        try {
          const updateData = { username, display_name: displayName, role };
          if (newPw) updateData.new_password = newPw;
          await api.auth.updateUser(userId, updateData);
          showToast('✅ 使用者资料已更新', 'success');
          document.getElementById(`upw-${userId}`).value = '';
          await loadUserList();
        } catch(err) {
          showToast('❌ 更新失败: ' + (err.message || ''), 'error');
        } finally {
          btn.disabled = false;
          btn.textContent = '💾 储存变更 (Save)';
        }
      });
    });
    
    // Delete user
    document.querySelectorAll('.delete-user-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const userId = e.currentTarget.dataset.id;
        const userName = e.currentTarget.dataset.name;
        if (!confirm(`确定要删除使用者「${userName}」吗？此操作无法撤销。`)) return;
        
        try {
          await api.auth.deleteUser(userId);
          showToast('✅ 使用者已删除', 'success');
          await loadUserList();
        } catch(err) {
          showToast('❌ 删除失败: ' + (err.message || ''), 'error');
        }
      });
    });
    
    // Add new user
    document.getElementById('add-user-btn')?.addEventListener('click', async () => {
      const displayName = document.getElementById('new-user-name').value.trim();
      const username = document.getElementById('new-user-login').value.trim();
      const password = document.getElementById('new-user-pw').value;
      const role = document.getElementById('new-user-role').value;
      
      if (!displayName || !username || !password) {
        showToast('❌ 请填写所有栏位', 'error');
        return;
      }
      
      const btn = document.getElementById('add-user-btn');
      btn.disabled = true;
      btn.textContent = '新增中...';
      try {
        await api.auth.register({ username, password, role, display_name: displayName, language: 'zh' });
        showToast('✅ 使用者新增成功！', 'success');
        await loadUserList();
      } catch(err) {
        showToast('❌ 新增失败: ' + (err.message || ''), 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = '新增使用者 (Create User)';
      }
    });
  } catch (e) {
    container.innerHTML = `<p style="color: var(--danger)">无法载入使用者</p>`;
  }
}


async function loadLineGroups() {
  const container = document.getElementById('line-groups-container');
  if (!container) return;
  
  try {
    const groups = await api.farms.getLineGroups();
    const farms = await api.farms.list();
    
    if (!groups || groups.length === 0) {
      container.innerHTML = `<p class="text-secondary text-sm">目前没有加入任何 LINE 群组。</p>`;
      return;
    }
    
    container.innerHTML = groups.map(g => {
      const currentFarm = farms.find(f => f.id === g.farm_id);
      
      let farmOptions = farms.map(f => {
        const selected = f.id === g.farm_id ? 'selected' : '';
        return `<option value="${f.id}" ${selected}>${f.name}</option>`;
      }).join('');
      
      return `
      <div style="padding: 1rem; border-bottom: 1px solid var(--border-color);">
        <div style="margin-bottom: 0.5rem; font-weight: 600;">
          群组名称: ${g.group_name || '(未知群组)'}
        </div>
        <div class="text-secondary text-sm" style="margin-bottom: 0.5rem; word-break: break-all;">
          当前连结: ${currentFarm ? currentFarm.name : '<span style="color:var(--danger)">未连结</span>'}
        </div>
        <div style="display: flex; gap: 0.5rem;">
          <select id="bind-farm-${g.line_group_id}" class="form-input" style="flex: 1; padding: 0.5rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
            <option value="">(选择新菜园连结)...</option>
            ${farmOptions}
          </select>
          <button class="btn btn-primary bind-group-btn" data-id="${g.line_group_id}" data-name="${g.group_name}" style="padding: 0.5rem 1rem; background: var(--primary); color: white; border: none; border-radius: var(--radius-sm); cursor: pointer;">
            更新连结
          </button>
        </div>
      </div>
    `}).join('');
    
    document.querySelectorAll('.bind-group-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const groupId = e.target.dataset.id;
        const groupName = e.target.dataset.name;
        const selectEl = document.getElementById(`bind-farm-${groupId}`);
        const farmId = parseInt(selectEl.value);
        
        if (!farmId) {
          showToast('请选择菜园', 'error');
          return;
        }
        
        btn.disabled = true;
        try {
          await api.farms.linkGroup({ line_group_id: groupId, farm_id: farmId, group_name: groupName });
          showToast('连结更新成功，机器人已发通知', 'success');
          await loadLineGroups(); // Refresh
        } catch(err) {
          showToast('更新连结失败', 'error');
          btn.disabled = false;
        }
      });
    });
  } catch (e) {
    container.innerHTML = `<p style="color: var(--danger)">无法载入群组列表</p>`;
  }
}

async function initZoneManagement() {
  const select = document.getElementById('zone-farm-select');
  const btn = document.getElementById('add-zone-btn');
  
  if (!select) return;
  
  try {
    const farms = await api.farms.list();
    if (!farms || farms.length === 0) {
      select.innerHTML = '<option value="">(无农场)</option>';
      return;
    }
    
    select.innerHTML = '<option value="">选择农场以管理区域...</option>' + 
      farms.map(f => `<option value="${f.id}">${f.name}</option>`).join('');
      
    select.addEventListener('change', async (e) => {
      const farmId = e.target.value;
      btn.disabled = !farmId;
      if (farmId) {
        await loadZones(farmId);
      } else {
        document.getElementById('zone-list-container').innerHTML = '<div class="text-secondary text-sm text-center" style="padding: 1rem;">请先选择上方的农场</div>';
      }
    });
    
    // Add zone
    btn.addEventListener('click', async () => {
      const farmId = select.value;
      const parent = document.getElementById('new-zone-parent').value.trim();
      const name = document.getElementById('new-zone-name').value.trim();
      
      if (!name) {
        showToast('❌ 必须填写子区域名称', 'error');
        return;
      }
      
      btn.disabled = true;
      btn.textContent = '新增中...';
      
      try {
        await api.farms.createZone(farmId, { 
          name: name,
          parent_zone: parent || null
        });
        showToast('✅ 区域新增成功', 'success');
        document.getElementById('new-zone-parent').value = '';
        document.getElementById('new-zone-name').value = '';
        await loadZones(farmId);
      } catch (err) {
        showToast('❌ 新增失败: ' + (err.message || ''), 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = '新增区域 (Create Zone)';
      }
    });
    
  } catch (err) {
    select.innerHTML = '<option value="">载入失败</option>';
  }
}

async function loadZones(farmId) {
  const container = document.getElementById('zone-list-container');
  container.innerHTML = '<div class="text-center text-sm" style="padding: 1rem;">载入中...</div>';
  
  try {
    const zones = await api.farms.listZones(farmId);
    if (!zones || zones.length === 0) {
      container.innerHTML = '<div class="text-secondary text-sm text-center" style="padding: 1rem;">该农场目前没有设定任何区域。</div>';
      return;
    }
    
    container.innerHTML = zones.map(z => `
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; border-bottom: 1px solid var(--border-color);">
        <div>
          ${z.parent_zone ? `<span class="badge badge-info" style="font-size: 0.7rem; margin-right: 0.3rem;">${z.parent_zone}</span>` : ''}
          <span style="font-weight: 500;">${z.name}</span>
        </div>
        <button class="icon-btn delete-zone-btn" data-id="${z.id}" style="color: var(--danger); font-size: 1rem;" title="删除区域">🗑️</button>
      </div>
    `).join('');
    
    document.querySelectorAll('.delete-zone-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const zoneId = e.currentTarget.dataset.id;
        if (!confirm('确定要删除此区域吗？')) return;
        
        try {
          await api.farms.deleteZone(zoneId);
          showToast('✅ 区域已删除', 'success');
          await loadZones(farmId);
        } catch (err) {
          showToast('❌ 删除失败: ' + (err.message || ''), 'error');
        }
      });
    });
    
  } catch (err) {
    container.innerHTML = '<div class="text-danger text-sm text-center" style="padding: 1rem;">载入区域失败</div>';
  }
}


async function initCropManagement() {
  const select = document.getElementById('crop-farm-select');
  const btn = document.getElementById('add-crop-btn');
  if (!select) return;
  
  try {
    const farms = await api.farms.list();
    if (!farms || farms.length === 0) {
      select.innerHTML = '<option value="">(无农场)</option>';
      return;
    }
    
    select.innerHTML = '<option value="">选择农场以管理作物...</option>' + 
      farms.map(f => `<option value="${f.id}">${f.name}</option>`).join('');
      
    select.addEventListener('change', async (e) => {
      const farmId = e.target.value;
      btn.disabled = !farmId;
      if (farmId) {
        await loadCrops(farmId);
      } else {
        document.getElementById('crop-list-container').innerHTML = '<div class="text-secondary text-sm text-center" style="padding: 1rem;">请先选择上方的农场</div>';
      }
    });
    
    btn.addEventListener('click', async () => {
      const farmId = select.value;
      const name = document.getElementById('new-crop-name').value.trim();
      const grow_days = parseInt(document.getElementById('new-crop-grow').value) || 0;
      const duration = parseInt(document.getElementById('new-crop-duration').value) || 1;
      const is_perennial = document.getElementById('new-crop-perennial').checked;
      
      if (!name) { showToast('❌ 必须填写作物名称', 'error'); return; }
      
      btn.disabled = true;
      btn.textContent = '新增中...';
      try {
        await api.farms.createCrop(farmId, { name, grow_days, harvest_duration_days: duration, is_perennial });
        showToast('✅ 作物新增成功', 'success');
        document.getElementById('new-crop-name').value = '';
        await loadCrops(farmId);
      } catch (err) {
        showToast('❌ 新增失败: ' + (err.message || ''), 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = '新增作物 (Create Crop)';
      }
    });
  } catch (err) {
    select.innerHTML = '<option value="">载入失败</option>';
  }
}

async function loadCrops(farmId) {
  const container = document.getElementById('crop-list-container');
  container.innerHTML = '<div class="text-center text-sm" style="padding: 1rem;">载入中...</div>';
  
  try {
    const crops = await api.farms.listCrops(farmId);
    if (!crops || crops.length === 0) {
      container.innerHTML = '<div class="text-secondary text-sm text-center" style="padding: 1rem;">该农场目前没有设定任何作物。</div>';
      return;
    }
    
    container.innerHTML = crops.map(c => `
      <div style="padding: 1rem; border-bottom: 1px solid var(--border-color);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
          <span style="font-weight: 600; color: var(--primary); font-size: 1.1rem;">${c.name} ${c.is_perennial ? '<span class="badge badge-info" style="font-size:0.7rem;">多年生</span>' : ''}</span>
          <button class="icon-btn delete-crop-btn" data-id="${c.id}" style="color: var(--danger);" title="删除">🗑️</button>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem;">
            <div>
                <label class="text-secondary text-sm">生长天数</label>
                <input type="number" id="cgrow-${c.id}" value="${c.grow_days}" class="form-input" style="width:100%; padding:0.3rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
            </div>
            <div>
                <label class="text-secondary text-sm">采收期 (天)</label>
                <input type="number" id="cdur-${c.id}" value="${c.harvest_duration_days}" class="form-input" style="width:100%; padding:0.3rem; border-radius: var(--radius-sm); border: 1px solid rgba(0,0,0,0.1);">
            </div>
        </div>
        <button class="btn btn-secondary save-crop-btn" data-id="${c.id}" style="width:100%; padding:0.4rem; margin-top:0.5rem; border-radius:var(--radius-sm); cursor:pointer;">
            💾 储存变更
        </button>
      </div>
    `).join('');
    
    document.querySelectorAll('.save-crop-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const cropId = e.currentTarget.dataset.id;
            const grow = parseInt(document.getElementById(`cgrow-${cropId}`).value) || 0;
            const dur = parseInt(document.getElementById(`cdur-${cropId}`).value) || 1;
            btn.textContent = '储存中...';
            try {
                await api.farms.updateCrop(cropId, { grow_days: grow, harvest_duration_days: dur });
                showToast('✅ 变更已储存', 'success');
                btn.textContent = '💾 储存变更';
            } catch(e) {
                showToast('❌ 储存失败', 'error');
                btn.textContent = '💾 储存变更';
            }
        });
    });

    document.querySelectorAll('.delete-crop-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const cropId = e.currentTarget.dataset.id;
        if (!confirm('确定要删除此作物设定吗？')) return;
        try {
          await api.farms.deleteCrop(cropId);
          showToast('✅ 作物已删除', 'success');
          await loadCrops(farmId);
        } catch (err) {
          showToast('❌ 删除失败', 'error');
        }
      });
    });
  } catch (err) {
    container.innerHTML = '<div class="text-danger text-sm text-center" style="padding: 1rem;">载入作物失败</div>';
  }
}

async function initSOPManagement() {
  var select = document.getElementById('sop-farm-select');
  var btn = document.getElementById('add-sop-btn');
  if (!select) return;
  
  try {
    var farms = await api.farms.list();
    if (!farms || farms.length === 0) {
      select.innerHTML = '<option value="">(No farms)</option>';
      return;
    }
    
    select.innerHTML = '<option value="">Select farm to manage SOPs...</option>' + 
      farms.map(function(f) { return '<option value="' + f.id + '">' + f.name + '</option>'; }).join('');
      
    select.addEventListener('change', async function(e) {
      var farmId = e.target.value;
      btn.disabled = !farmId;
      if (farmId) {
        await loadSOPs(farmId);
      } else {
        document.getElementById('sop-list-container').innerHTML = '<div class="text-secondary text-sm text-center" style="padding: 1rem;">Select a farm above</div>';
      }
    });
    
    btn.addEventListener('click', async function() {
      var farmId = select.value;
      var title = document.getElementById('new-sop-title').value.trim();
      var desc = document.getElementById('new-sop-desc').value.trim();
      var role = document.getElementById('new-sop-role').value;
      
      if (!title) { showToast('Please enter a task title', 'error'); return; }
      
      btn.disabled = true;
      btn.textContent = 'Creating...';
      try {
        var token = localStorage.getItem('fw_token');
        var resp = await fetch('/api/tasks/recurring', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
          body: JSON.stringify({
            farm_id: parseInt(farmId),
            title: title,
            description: desc || title,
            target_role: role,
            cron_expression: '0 6 * * *',
            is_active: true
          })
        });
        if (!resp.ok) throw new Error('Failed');
        showToast('SOP task created!', 'success');
        document.getElementById('new-sop-title').value = '';
        document.getElementById('new-sop-desc').value = '';
        await loadSOPs(farmId);
      } catch (err) {
        showToast('Failed to create SOP', 'error');
      } finally {
        btn.disabled = false;
        btn.textContent = 'Add SOP Task';
      }
    });
  } catch (err) {
    select.innerHTML = '<option value="">Load failed</option>';
  }
}

async function loadSOPs(farmId) {
  var container = document.getElementById('sop-list-container');
  container.innerHTML = '<div class="text-center text-sm" style="padding: 1rem;">Loading...</div>';
  
  try {
    var token = localStorage.getItem('fw_token');
    var resp = await fetch('/api/tasks/recurring?farm_id=' + farmId, {
      headers: { 'Authorization': 'Bearer ' + token }
    });
    if (!resp.ok) throw new Error('Failed');
    var sops = await resp.json();
    
    if (!sops || sops.length === 0) {
      container.innerHTML = '<div class="text-secondary text-sm text-center" style="padding: 1rem;">No SOP tasks defined for this farm.</div>';
      return;
    }
    
    var html = '';
    sops.forEach(function(s) {
      var roleLabel = s.target_role === 'foreman' ? '<span class="badge" style="background:#8b5cf6;color:white;font-size:0.7rem;">FOREMAN</span>' : '<span class="badge badge-info" style="font-size:0.7rem;">WORKER</span>';
      var activeLabel = s.is_active ? '<span style="color:var(--primary);">Active</span>' : '<span style="color:var(--danger);">Inactive</span>';
      html += '<div style="display: flex; justify-content: space-between; align-items: center; padding: 0.8rem; border-bottom: 1px solid var(--border-color);">';
      html += '<div>';
      html += '<div style="font-weight:600;">' + roleLabel + ' ' + s.title + '</div>';
      html += '<div class="text-secondary text-sm">' + (s.description || '') + '</div>';
      html += '<div class="text-secondary text-sm">' + activeLabel + '</div>';
      html += '</div>';
      html += '<button class="icon-btn delete-sop-btn" data-id="' + s.id + '" style="color: var(--danger);" title="Delete">&#x1F5D1;&#xFE0F;</button>';
      html += '</div>';
    });
    
    container.innerHTML = html;
    
    document.querySelectorAll('.delete-sop-btn').forEach(function(btn) {
      btn.addEventListener('click', async function(e) {
        var sopId = e.currentTarget.dataset.id;
        if (!confirm('Delete this SOP task?')) return;
        try {
          var token = localStorage.getItem('fw_token');
          var resp = await fetch('/api/tasks/recurring/' + sopId, {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + token }
          });
          if (!resp.ok) throw new Error('Failed');
          showToast('SOP task deleted', 'success');
          await loadSOPs(farmId);
        } catch (err) {
          showToast('Delete failed', 'error');
        }
      });
    });
  } catch (err) {
    container.innerHTML = '<div class="text-danger text-sm text-center" style="padding: 1rem;">Failed to load SOPs</div>';
  }
}

