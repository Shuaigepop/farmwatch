import sys

with open('frontend/js/components/settings.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Crop Management HTML inside the last div
crop_html = """
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
"""

content = content.replace('    </div>\n  `;', crop_html + '    </div>\n  `;')

# Add initCropManagement calls
content = content.replace('await initZoneManagement();', 'await initZoneManagement();\n  await initCropManagement();')

# Append the javascript functions for crops
crop_js = """
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
"""

with open('frontend/js/components/settings.js', 'w', encoding='utf-8') as f:
    f.write(content + '\n' + crop_js)
print("Updated settings.js")
