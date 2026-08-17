import sys

with open('frontend/js/components/progress.js', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add "Log Planting" button next to "New Task" button
old_btns = '''
          ${(user.role === 'boss' || user.role === 'supervisor') && farmId ? `
          <button class="btn btn-primary" id="show-create-task-btn">
            ➕ 新增任务 (New Task)
          </button>
          ` : ''}
'''

new_btns = '''
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
'''
content = content.replace(old_btns, new_btns)

# 2. Add "Log Planting" form
old_form = '''
        <div id="create-task-form-container" class="glass-panel" style="display: none; padding: 1.5rem; margin-bottom: 2rem;">
'''

new_form = '''
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
'''
content = content.replace(old_form, new_form)

# 3. Add JS Logic for the planting form
old_js = '''
    // Submit form
    const form = document.getElementById('create-task-form');
'''

new_js = '''
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
'''
content = content.replace(old_js, new_js)

# Also fix the cancel logic for New Task button to show the Plant button again
old_cancel_js = '''
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        formContainer.style.display = 'none';
        showBtn.style.display = 'inline-block';
      });
    }
'''

new_cancel_js = '''
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        formContainer.style.display = 'none';
        if (showBtn) showBtn.style.display = 'inline-block';
        if (document.getElementById('show-plant-btn')) document.getElementById('show-plant-btn').style.display = 'inline-block';
      });
    }
'''
content = content.replace(old_cancel_js, new_cancel_js)

old_show_js = '''
    if (showBtn) {
      showBtn.addEventListener('click', () => {
        formContainer.style.display = 'block';
        showBtn.style.display = 'none';
      });
    }
'''

new_show_js = '''
    if (showBtn) {
      showBtn.addEventListener('click', () => {
        formContainer.style.display = 'block';
        if (showBtn) showBtn.style.display = 'none';
        if (document.getElementById('show-plant-btn')) document.getElementById('show-plant-btn').style.display = 'none';
      });
    }
'''
content = content.replace(old_show_js, new_show_js)

with open('frontend/js/components/progress.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated progress.js successfully")
