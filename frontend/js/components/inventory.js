import { t } from '../i18n.js';
import { auth } from '../auth.js';
import { api, showToast } from '../api.js';

export async function renderInventory(container) {
  const user = auth.getUser();

  container.innerHTML = `
    <div class="page-container slide-in">
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 1.5rem; flex-wrap: wrap; gap: 1rem;">
        <h2>📦 ${t('nav.inventory') || '库存与收成'}</h2>
        <div style="display:flex; gap: 0.5rem;">
          <button class="btn btn-primary" id="add-inventory-btn" style="padding: 0.6rem 1.2rem; font-size: 0.9rem; width:auto;">+ 新增库存</button>
          <button class="btn btn-primary" id="add-harvest-btn" style="padding: 0.6rem 1.2rem; font-size: 0.9rem; width:auto; background: var(--accent);">+ 新增收成计画</button>
        </div>
      </div>

      <!-- Inventory Section -->
      <div class="section-title" style="margin-top: 1.5rem;">📦 现有库存 (Inventory)</div>
      <div id="inventory-table-container" style="overflow-x: auto;">
        <div class="skeleton" style="height: 200px; width: 100%;"></div>
      </div>

      <!-- Harvest Plan Section -->
      <div class="section-title" style="margin-top: 2.5rem;">📅 收成计画 (Harvest Plans)</div>
      <div id="harvest-table-container" style="overflow-x: auto;">
        <div class="skeleton" style="height: 200px; width: 100%;"></div>
      </div>

      <!-- Add Inventory Modal -->
      <div id="inventory-modal" class="modal-overlay" style="display:none;">
        <div class="glass-panel" style="padding: 2rem; max-width: 500px; width: 90%; margin: auto;">
          <h3 id="modal-title">新增库存</h3>
          <form id="inventory-form" style="margin-top: 1rem;">
            <input type="hidden" id="inv-id">
            <div class="form-group">
              <label class="form-label">菜园</label>
              <select id="inv-farm" class="form-input" required></select>
            </div>
            <div class="form-group">
              <label class="form-label">种类 (Type)</label>
              <select id="inv-type" class="form-input" required>
                <option value="seed">🌱 种子 (Seed)</option>
                <option value="pesticide">🧪 农药 (Pesticide)</option>
                <option value="fertilizer">💩 肥料 (Fertilizer)</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">名称 (Name)</label>
              <input type="text" id="inv-name" class="form-input" required placeholder="例如：小白菜种子、甲胺磷">
            </div>
            <div style="display:flex; gap: 1rem;">
              <div class="form-group" style="flex:1;">
                <label class="form-label">数量 (Quantity)</label>
                <input type="number" id="inv-qty" class="form-input" required step="0.01" min="0">
              </div>
              <div class="form-group" style="flex:1;">
                <label class="form-label">单位 (Unit)</label>
                <input type="text" id="inv-unit" class="form-input" required placeholder="kg / L / 包">
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">备注 (Notes)</label>
              <input type="text" id="inv-notes" class="form-input" placeholder="选填">
            </div>
            <div style="display:flex; gap: 1rem; margin-top: 1rem;">
              <button type="submit" class="btn btn-primary" style="flex:1;">储存</button>
              <button type="button" class="btn" id="inv-cancel" style="flex:1; background: var(--bg-color); border: 1px solid var(--border-color);">取消</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Add Harvest Modal -->
      <div id="harvest-modal" class="modal-overlay" style="display:none;">
        <div class="glass-panel" style="padding: 2rem; max-width: 500px; width: 90%; margin: auto;">
          <h3>新增收成计画</h3>
          <form id="harvest-form" style="margin-top: 1rem;">
            <input type="hidden" id="hv-id">
            <div class="form-group">
              <label class="form-label">菜园</label>
              <select id="hv-farm" class="form-input" required></select>
            </div>
            <div class="form-group">
              <label class="form-label">作物名称 (Crop)</label>
              <input type="text" id="hv-crop" class="form-input" required placeholder="例如：小白菜">
            </div>
            <div style="display:flex; gap: 1rem;">
              <div class="form-group" style="flex:1;">
                <label class="form-label">种植日期</label>
                <input type="date" id="hv-planted" class="form-input" required>
              </div>
              <div class="form-group" style="flex:1;">
                <label class="form-label">预计收成日期</label>
                <input type="date" id="hv-harvest" class="form-input" required>
              </div>
            </div>
            <div class="form-group">
              <label class="form-label">区域 (Zone)</label>
              <input type="text" id="hv-zone" class="form-input" placeholder="例如：A区">
            </div>
            <div class="form-group">
              <label class="form-label">状态 (Status)</label>
              <select id="hv-status" class="form-input" required>
                <option value="growing">🌱 生长中</option>
                <option value="harvested">✅ 已收成</option>
                <option value="failed">❌ 失败</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">备注 (Notes)</label>
              <input type="text" id="hv-notes" class="form-input" placeholder="选填">
            </div>
            <div style="display:flex; gap: 1rem; margin-top: 1rem;">
              <button type="submit" class="btn btn-primary" style="flex:1;">储存</button>
              <button type="button" class="btn" id="hv-cancel" style="flex:1; background: var(--bg-color); border: 1px solid var(--border-color);">取消</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `;

  // Load farms into selectors
  let farms = [];
  try { farms = await api.farms.list(); } catch(e) { farms = []; }
  const farmOptions = farms.map(f => `<option value="${f.id}">${f.name}</option>`).join('');
  document.getElementById('inv-farm').innerHTML = farmOptions;
  document.getElementById('hv-farm').innerHTML = farmOptions;

  // Get farm ID
  const globalFarmSelect = document.getElementById('global-farm-select');
  const selectedFarmId = (globalFarmSelect && globalFarmSelect.value !== 'all') ? parseInt(globalFarmSelect.value) : (user ? user.farmId : null);

  window.currentFarmId = selectedFarmId; // store globally for events

  // Load data
  await loadInventory(selectedFarmId);
  await loadHarvestPlans(selectedFarmId);

  // Modal open/close
  document.getElementById('add-inventory-btn').addEventListener('click', () => {
    document.getElementById('inv-id').value = '';
    document.getElementById('inventory-form').reset();
    if (window.currentFarmId) document.getElementById('inv-farm').value = window.currentFarmId;
    document.getElementById('inventory-modal').style.display = 'flex';
  });
  document.getElementById('inv-cancel').addEventListener('click', () => {
    document.getElementById('inventory-modal').style.display = 'none';
  });
  document.getElementById('add-harvest-btn').addEventListener('click', () => {
    document.getElementById('hv-id').value = '';
    document.getElementById('harvest-form').reset();
    if (window.currentFarmId) document.getElementById('hv-farm').value = window.currentFarmId;
    document.getElementById('harvest-modal').style.display = 'flex';
  });
  document.getElementById('hv-cancel').addEventListener('click', () => {
    document.getElementById('harvest-modal').style.display = 'none';
  });

  // Inventory form submit
  document.getElementById('inventory-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const id = document.getElementById('inv-id').value;
      const data = {
        farm_id: parseInt(document.getElementById('inv-farm').value),
        item_type: document.getElementById('inv-type').value,
        name: document.getElementById('inv-name').value,
        quantity: parseFloat(document.getElementById('inv-qty').value),
        unit: document.getElementById('inv-unit').value,
        notes: document.getElementById('inv-notes').value || null,
      };
      
      if (id) {
        await api.inventory.update(id, data);
        showToast('成功更新库存', 'success');
      } else {
        await api.inventory.create(data.farm_id, data);
        showToast('成功新增库存', 'success');
      }
      
      document.getElementById('inventory-modal').style.display = 'none';
      document.getElementById('inventory-form').reset();
      await loadInventory(window.currentFarmId);
    } catch(err) { /* toast already shown */ }
  });

  // Harvest form submit
  document.getElementById('harvest-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const id = document.getElementById('hv-id').value;
      const data = {
        farm_id: parseInt(document.getElementById('hv-farm').value),
        crop_name: document.getElementById('hv-crop').value,
        planted_date: document.getElementById('hv-planted').value,
        expected_harvest_date: document.getElementById('hv-harvest').value,
        area_or_zone: document.getElementById('hv-zone').value || null,
        status: document.getElementById('hv-status').value || 'growing',
        notes: document.getElementById('hv-notes').value || null,
      };
      
      if (id) {
        await api.inventory.updateHarvest(id, data);
        showToast('成功更新收成计画', 'success');
      } else {
        await api.inventory.createHarvest(data.farm_id, data);
        showToast('成功新增收成计画', 'success');
      }
      
      document.getElementById('harvest-modal').style.display = 'none';
      document.getElementById('harvest-form').reset();
      await loadHarvestPlans(window.currentFarmId);
    } catch(err) { /* toast already shown */ }
  });
}

async function loadInventory(farmId) {
  const container = document.getElementById('inventory-table-container');
  if (!farmId) { container.innerHTML = "<div style=\"padding:1rem\">请先在左侧选择特定菜园。</div>"; return; }
  
  try {
    const items = await api.inventory.list(farmId); window._invItems = items;
    if (!items || items.length === 0) {
      container.innerHTML = `<div style="text-align:center; padding: 2rem; color: var(--text-secondary);">目前没有任何库存资料。您可以点击右上角按钮新增。</div>`;
      return;
    }
    const typeIcons = { seed: '🌱', pesticide: '🧪', fertilizer: '💩' };
    const typeLabels = { seed: '种子', pesticide: '农药', fertilizer: '肥料' };
    container.innerHTML = `
      <table style="width:100%; border-collapse: collapse; background: var(--surface); border-radius: var(--radius-md); overflow: hidden; box-shadow: var(--shadow-sm);">
        <thead>
          <tr style="background: var(--primary); color: white; text-align: left;">
            <th style="padding: 0.75rem 1rem;">种类</th>
            <th style="padding: 0.75rem 1rem;">名称</th>
            <th style="padding: 0.75rem 1rem;">数量</th>
            <th style="padding: 0.75rem 1rem;">备注</th>
            <th style="padding: 0.75rem 1rem;">最后更新时间</th>
            <th style="padding: 0.75rem 1rem;">操作</th>
          </tr>
        </thead>
        <tbody>
          ${items.map(item => {
            const isLow = item.quantity < 10;
            return `
              <tr style="border-bottom: 1px solid var(--border-color); ${isLow ? 'background: #FFF3E0;' : ''}">
                <td style="padding: 0.75rem 1rem;">${typeIcons[item.item_type] || '📦'} ${typeLabels[item.item_type] || item.item_type}</td>
                <td style="padding: 0.75rem 1rem; font-weight: 600;">${item.name}</td>
                <td style="padding: 0.75rem 1rem;">
                  <span style="font-weight: 700; color: ${isLow ? 'var(--danger)' : 'var(--primary)'};">${item.quantity}</span> ${item.unit}
                  ${isLow ? ' <span class="tag tag-warning">库存低</span>' : ''}
                </td>
                <td style="padding: 0.75rem 1rem; color: var(--text-secondary);">${item.notes || '-'}</td>
                <td style="padding: 0.75rem 1rem; color: var(--text-secondary); font-size: 0.85rem;">${item.updated_at ? new Date(item.updated_at).toLocaleDateString() : '-'}</td>
                <td style="padding: 0.75rem 1rem;">
                  <button class="btn btn-sm btn-primary edit-inv-btn" data-id="${item.id}" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;">编辑</button>
                  <button class="btn btn-sm btn-danger delete-inv-btn" data-id="${item.id}" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;">删除</button>
                </td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    `;
  } catch(err) {
    console.error('loadInventory error:', err);
    container.innerHTML = `<div style="padding: 1rem; color: var(--danger);">
      加载库存失败: ${err.message || '未知错误'}
      <br><button class="btn btn-sm btn-primary" onclick="location.reload()" style="margin-top: 0.5rem;">🔄 重新整理</button>
    </div>`;
  }

  // Attach handlers
  container.querySelectorAll('.edit-inv-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const id = e.target.getAttribute('data-id');
      const item = window._invItems.find(i => i.id == id);
      if (item) {
        document.getElementById('inv-id').value = item.id;
        document.getElementById('inv-farm').value = item.farm_id;
        document.getElementById('inv-type').value = item.item_type;
        document.getElementById('inv-name').value = item.name;
        document.getElementById('inv-qty').value = item.quantity;
        document.getElementById('inv-unit').value = item.unit;
        document.getElementById('inv-notes').value = item.notes || '';
        document.getElementById('inventory-modal').style.display = 'flex';
      }
    });
  });
  container.querySelectorAll('.delete-inv-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      if(confirm('确定要删除此库存吗？')) {
        const id = e.target.getAttribute('data-id');
        try {
          await api.inventory.delete(id);
          showToast('库存已删除', 'success');
          await loadInventory(window.currentFarmId);
        } catch(err) {}
      }
    });
  });
}

async function loadHarvestPlans(farmId) {
  const container = document.getElementById('harvest-table-container');
  if (!farmId) { container.innerHTML = "<div style=\"padding:1rem\">请先在左侧选择特定菜园。</div>"; return; }
  
  try {
    const plans = await api.inventory.listHarvest(farmId); window._hvPlans = plans;
    if (!plans || plans.length === 0) {
      container.innerHTML = `<div style="text-align:center; padding: 2rem; color: var(--text-secondary);">目前没有任何收成计画。您可以点击右上角按钮新增。</div>`;
      return;
    }
    const statusLabels = { growing: '🌱 生长中', harvested: '✅ 已收成', failed: '❌ 失败' };
    container.innerHTML = `
      <table style="width:100%; border-collapse: collapse; background: var(--surface); border-radius: var(--radius-md); overflow: hidden; box-shadow: var(--shadow-sm);">
        <thead>
          <tr style="background: var(--accent); color: white; text-align: left;">
            <th style="padding: 0.75rem 1rem;">作物名称</th>
            <th style="padding: 0.75rem 1rem;">区域</th>
            <th style="padding: 0.75rem 1rem;">种植日期</th>
            <th style="padding: 0.75rem 1rem;">预计收成日期</th>
            <th style="padding: 0.75rem 1rem;">状态</th>
            <th style="padding: 0.75rem 1rem;">备注</th>
            <th style="padding: 0.75rem 1rem;">操作</th>
          </tr>
        </thead>
        <tbody>
          ${plans.map(p => {
            const today = new Date().toISOString().split('T')[0];
            const isOverdue = p.expected_harvest_date && p.expected_harvest_date < today && p.status === 'growing';
            return `
              <tr style="border-bottom: 1px solid var(--border-color); ${isOverdue ? 'background: #FFEBEE;' : ''}">
                <td style="padding: 0.75rem 1rem; font-weight: 600;">🍅 ${p.crop_name}</td>
                <td style="padding: 0.75rem 1rem;">${p.area_or_zone || '-'}</td>
                <td style="padding: 0.75rem 1rem;">${p.planted_date || '-'}</td>
                <td style="padding: 0.75rem 1rem; font-weight: 600; color: ${isOverdue ? 'var(--danger)' : 'inherit'};">
                  ${p.expected_harvest_date || '-'} ${isOverdue ? '（已逾期）' : ''}
                </td>
                <td style="padding: 0.75rem 1rem;">${statusLabels[p.status] || p.status}</td>
                <td style="padding: 0.75rem 1rem; color: var(--text-secondary);">${p.notes || '-'}</td>
                <td style="padding: 0.75rem 1rem;">
                  <button class="btn btn-sm btn-primary edit-hv-btn" data-id="${p.id}" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;">编辑</button>
                  <button class="btn btn-sm btn-danger delete-hv-btn" data-id="${p.id}" style="padding: 0.2rem 0.5rem; font-size: 0.8rem;">删除</button>
                </td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    `;
  } catch(err) {
    console.error('loadHarvestPlans error:', err);
    container.innerHTML = `<div style="padding: 1rem; color: var(--danger);">
      加载收成计划失败: ${err.message || '未知错误'}
      <br><button class="btn btn-sm btn-primary" onclick="location.reload()" style="margin-top: 0.5rem;">🔄 重新整理</button>
    </div>`;
  }

  // Attach handlers
  container.querySelectorAll('.edit-hv-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const id = e.target.getAttribute('data-id');
      const plan = window._hvPlans.find(i => i.id == id);
      if (plan) {
        document.getElementById('hv-id').value = plan.id;
        document.getElementById('hv-farm').value = plan.farm_id;
        document.getElementById('hv-crop').value = plan.crop_name;
        document.getElementById('hv-planted').value = plan.planted_date;
        document.getElementById('hv-harvest').value = plan.expected_harvest_date;
        document.getElementById('hv-zone').value = plan.area_or_zone || '';
        document.getElementById('hv-status').value = plan.status || 'growing';
        document.getElementById('hv-notes').value = plan.notes || '';
        document.getElementById('harvest-modal').style.display = 'flex';
      }
    });
  });
  container.querySelectorAll('.delete-hv-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      if(confirm('确定要删除此计画吗？')) {
        const id = e.target.getAttribute('data-id');
        try {
          await api.inventory.deleteHarvest(id);
          showToast('计画已删除', 'success');
          await loadHarvestPlans(window.currentFarmId);
        } catch(err) {}
      }
    });
  });
}
