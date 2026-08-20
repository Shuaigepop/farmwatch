import { apiFetch, api } from '../api.js';

export async function renderScheduler(container) {
  let currentTasks = [];
  let scheduleStatus = "none";
  let loading = false;
  let zones = [];
  
  const farmId = localStorage.getItem('fw_selected_farm');
  
  async function loadData() {
    if (!farmId || farmId === 'all') {
      container.innerHTML = `<div class="page-container"><p>Please select a specific farm first.</p></div>`;
      return;
    }
    
    try {
      loading = true;
      render();
      zones = await api.farms.listZones(farmId);
      const data = await apiFetch(`/schedules/${farmId}/today`);
      scheduleStatus = data.status;
      if (data.status !== "none") {
        currentTasks = data.tasks;
      }
    } catch (e) {
      console.error(e);
      container.innerHTML = `<div class="page-container"><p>Error loading schedule.</p></div>`;
    } finally {
      loading = false;
      render();
    }
  }
  
  async function handleGenerate() {
    loading = true;
    render();
    try {
      await apiFetch(`/schedules/${farmId}/generate`, { method: 'POST' });
      await loadData();
    } catch (e) {
      console.error(e);
      const msg = e.message || "Unknown error";
      alert("Error generating schedule:\n" + msg);
      loading = false;
      render();
    }
  }
  
  async function handleApprove() {
    try {
      const tbody = container.querySelector('#draft-tbody');
      const rows = tbody.querySelectorAll('tr');
      const updatedTasks = [];
      
      rows.forEach((tr) => {
        const titleInput = tr.querySelector('.task-title-input');
        const descInput = tr.querySelector('.task-desc-input');
        const zoneSelect = tr.querySelector('.task-zone-select');
        
        if (titleInput && titleInput.value.trim() !== '') {
            updatedTasks.push({
              title: titleInput.value.trim(),
              description: descInput ? descInput.value.trim() : '',
              zone_id: (zoneSelect && zoneSelect.value) ? parseInt(zoneSelect.value) : null
            });
        }
      });
      
      if (updatedTasks.length === 0) {
          alert("无法派发空白表单，请确认有填写任务标题 (Cannot approve empty schedule)");
          return;
      }
      
      loading = true;
      render();
      
      await apiFetch(`/schedules/${farmId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tasks: updatedTasks })
      });
      
      alert("Schedule approved and sent to LINE!");
      await loadData();
    } catch (e) {
      console.error(e);
      alert("Error approving schedule");
      loading = false;
      render();
    }
  }
  
  let dragSrcEl = null;

  function render() {
    if (!farmId || farmId === 'all') return;
    
    let html = `<div class="page-container">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
        <h2 style="margin: 0;">AI Daily Scheduler</h2>
        <div>
            <button class="btn btn-secondary" id="btn-trigger-6pm" style="margin-right: 10px;">测试 6PM 查帐</button>
            <button class="btn btn-secondary" id="btn-trigger-7pm">发送 7PM 总结</button>
        </div>
      </div>
      <div class="card" style="padding: 20px; overflow-x: auto;">
    `;
    
    if (loading) {
      html += `<p>Loading / Processing...</p>`;
    } else if (scheduleStatus === "none") {
      html += `
        <p>No schedule generated for today yet.</p>
        <button class="btn btn-primary" id="btn-generate">Generate AI Schedule</button>
      `;
    } else if (scheduleStatus === "approved") {
      html += `<p style="color: green; font-weight: bold;">Schedule has been approved and tasks have been created.</p>`;
      html += `<ul>`;
      currentTasks.forEach(t => {
        html += `<li><strong>${t.title}</strong> - ${t.description}</li>`;
      });
      html += `</ul>`;
      html += `
        <div style="margin-top: 20px; padding-top: 15px; border-top: 1px solid var(--border-color);">
            <button class="btn btn-warning" id="btn-revert" style="margin-right: 10px;">🔓 解除锁定 (Revert to Draft)</button>
            <button class="btn btn-primary" id="btn-generate">🔄 重新 AI 排程 (Regenerate AI Schedule)</button>
        </div>
      `;
    } else {
      // Draft mode - Excel like table
      html += `
        <p>Review the AI proposed schedule. You can edit directly in the table, drag the ☰ handle to reorder, or add/delete rows before approving.</p>
        <div style="min-width: 600px; border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; margin-top: 15px;">
        <table class="table" style="width: 100%; border-collapse: collapse; margin-bottom: 0;">
          <thead style="background: rgba(0,0,0,0.05); border-bottom: 2px solid var(--border-color);">
            <tr>
              <th style="width: 40px; text-align: center; padding: 10px;"></th>
              <th style="width: 150px; padding: 10px; text-align: left;">关联区域 (Zone)</th>
              <th style="width: 250px; padding: 10px; text-align: left;">任务标题 (Title)</th>
              <th style="padding: 10px; text-align: left;">详细说明 (Description)</th>
              <th style="width: 50px; text-align: center; padding: 10px;">操作</th>
            </tr>
          </thead>
          <tbody id="draft-tbody">
      `;
      
      currentTasks.forEach((t, idx) => {
        html += `
          <tr class="draggable-row" draggable="true" style="border-bottom: 1px solid var(--border-color); transition: background-color 0.2s;">
            <td class="drag-handle" style="text-align: center; color: #999; cursor: move; user-select: none; font-size: 1.2rem;">☰</td>
            <td style="padding: 5px;">
              <select class="form-control task-zone-select" style="width: 100%; border: none; background: transparent; padding: 8px;">
                <option value="">(无关联)</option>
                ${zones.map(z => `<option value="${z.id}" ${t.zone_id == z.id ? 'selected' : ''}>${z.parent_zone ? z.parent_zone + ' - ' : ''}${z.name}</option>`).join('')}
              </select>
            </td>
            <td style="padding: 5px;">
              <input type="text" class="form-control task-title-input" value="${t.title || ''}" style="width: 100%; border: none; background: transparent; padding: 8px; font-weight: 500;" placeholder="输入标题..." />
            </td>
            <td style="padding: 5px;">
              <input type="text" class="form-control task-desc-input" value="${t.description || ''}" style="width: 100%; border: none; background: transparent; padding: 8px;" placeholder="输入任务描述细节..." />
            </td>
            <td style="text-align: center; padding: 5px;">
              <button class="icon-btn text-danger btn-delete-row" style="padding: 4px; background: none; border: none; cursor: pointer; border-radius: 4px; transition: background-color 0.2s;">🗑️</button>
            </td>
          </tr>
        `;
      });
      
      html += `
          </tbody>
        </table>
        </div>
        <div style="margin-top: 10px;">
          <button class="btn btn-secondary" id="btn-add-row" style="padding: 4px 12px; font-size: 0.9em; background: transparent; border: 1px dashed var(--border-color); color: var(--text-secondary);">+ 新增一行 (Add Row)</button>
        </div>
        <div style="margin-top: 20px; padding-top: 15px;">
          <button class="btn btn-success" id="btn-approve" style="padding: 10px 20px; font-size: 1.1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">Approve & Dispatch 🚀</button>
        </div>
      `;
    }
    
    html += `</div></div>`;
    container.innerHTML = html;
    
    // Attach events
    const btnTrigger6pm = container.querySelector('#btn-trigger-6pm');
    if (btnTrigger6pm) btnTrigger6pm.addEventListener('click', async () => {
        try {
            await apiFetch(`/test/cron/6pm-check`, { method: 'POST' });
            alert("6PM 查帐排程已在背景执行！请查看 LINE 群组。(6PM check triggered)");
        } catch(e) {
            alert("Error triggering 6PM cron");
        }
    });

    const btnTrigger7pm = container.querySelector('#btn-trigger-7pm');
    if (btnTrigger7pm) btnTrigger7pm.addEventListener('click', async () => {
        try {
            await apiFetch(`/test/cron/7pm-summary`, { method: 'POST' });
            alert("7PM 总结与排程已在背景执行！请查看 LINE 群组。(7PM summary triggered)");
        } catch(e) {
            alert("Error triggering 7PM cron");
        }
    });

    const btnGenerate = container.querySelector('#btn-generate');
    if (btnGenerate) btnGenerate.addEventListener('click', handleGenerate);
    
    const btnRevert = container.querySelector('#btn-revert');
    if (btnRevert) btnRevert.addEventListener('click', async () => {
        if (!confirm("解除锁定后，您可以重新修改并派发。\n注意：先前已派发到看板的任务并不会自动删除，如有重复请至「任务与行程」手动删除。\n确定要解除锁定吗？")) return;
        try {
            loading = true;
            render();
            await apiFetch(`/schedules/${farmId}/revert`, { method: 'POST' });
            await loadData();
        } catch(e) {
            alert("Error reverting schedule");
            loading = false;
            render();
        }
    });
    
    const btnApprove = container.querySelector('#btn-approve');
    if (btnApprove) btnApprove.addEventListener('click', handleApprove);
    
    const btnAddRow = container.querySelector('#btn-add-row');
    if (btnAddRow) btnAddRow.addEventListener('click', () => {
        const tbody = container.querySelector('#draft-tbody');
        const tr = document.createElement('tr');
        tr.className = 'draggable-row';
        tr.setAttribute('draggable', 'true');
        tr.style = "border-bottom: 1px solid var(--border-color); transition: background-color 0.2s; background: rgba(0, 128, 0, 0.05);";
        tr.innerHTML = `
            <td class="drag-handle" style="text-align: center; color: #999; cursor: move; user-select: none; font-size: 1.2rem;">☰</td>
            <td style="padding: 5px;">
              <select class="form-control task-zone-select" style="width: 100%; border: none; background: transparent; padding: 8px;">
                <option value="">(无关联)</option>
                ${zones.map(z => `<option value="${z.id}">${z.parent_zone ? z.parent_zone + ' - ' : ''}${z.name}</option>`).join('')}
              </select>
            </td>
            <td style="padding: 5px;">
              <input type="text" class="form-control task-title-input" value="" style="width: 100%; border: none; background: transparent; padding: 8px; font-weight: 500;" placeholder="输入标题..." />
            </td>
            <td style="padding: 5px;">
              <input type="text" class="form-control task-desc-input" value="" style="width: 100%; border: none; background: transparent; padding: 8px;" placeholder="输入任务描述细节..." />
            </td>
            <td style="text-align: center; padding: 5px;">
              <button class="icon-btn text-danger btn-delete-row" style="padding: 4px; background: none; border: none; cursor: pointer; border-radius: 4px; transition: background-color 0.2s;">🗑️</button>
            </td>
        `;
        tbody.appendChild(tr);
        attachRowEvents(tr);
        
        // Remove highlight after a moment
        setTimeout(() => {
            tr.style.background = '';
        }, 1000);
    });
    
    // Attach drag and delete events to all rows
    const rows = container.querySelectorAll('.draggable-row');
    rows.forEach(row => attachRowEvents(row));
  }

  function attachRowEvents(row) {
      const delBtn = row.querySelector('.btn-delete-row');
      if (delBtn) {
          delBtn.addEventListener('click', () => {
              row.remove();
          });
          
          delBtn.addEventListener('mouseover', () => {
              delBtn.style.backgroundColor = 'rgba(255,0,0,0.1)';
          });
          delBtn.addEventListener('mouseout', () => {
              delBtn.style.backgroundColor = '';
          });
      }
      
      const inputs = row.querySelectorAll('input, select');
      inputs.forEach(input => {
          input.addEventListener('focus', () => {
             row.style.backgroundColor = 'rgba(0,0,0,0.02)';
          });
          input.addEventListener('blur', () => {
             row.style.backgroundColor = '';
          });
      });
      
      row.addEventListener('dragstart', function(e) {
          dragSrcEl = this;
          e.dataTransfer.effectAllowed = 'move';
          e.dataTransfer.setData('text/plain', 'dummy'); // Firefox requires data to be set
          this.style.opacity = '0.4';
      });
      
      row.addEventListener('dragover', function(e) {
          e.preventDefault(); 
          e.dataTransfer.dropEffect = 'move';
          return false;
      });
      
      row.addEventListener('dragenter', function(e) {
          if (this !== dragSrcEl) {
              this.style.borderTop = '2px solid var(--primary)';
          }
      });
      
      row.addEventListener('dragleave', function(e) {
          this.style.borderTop = '';
      });
      
      row.addEventListener('drop', function(e) {
          e.stopPropagation();
          this.style.borderTop = '';
          
          if (dragSrcEl !== this) {
              const tbody = row.parentNode;
              const allRows = Array.from(tbody.querySelectorAll('tr'));
              const srcIndex = allRows.indexOf(dragSrcEl);
              const targetIndex = allRows.indexOf(this);
              
              if (srcIndex < targetIndex) {
                  this.after(dragSrcEl);
              } else {
                  this.before(dragSrcEl);
              }
          }
          return false;
      });
      
      row.addEventListener('dragend', function(e) {
          this.style.opacity = '1';
          const rows = container.querySelectorAll('.draggable-row');
          rows.forEach(r => {
              r.style.borderTop = '';
          });
      });
  }
  
  await loadData();
}
