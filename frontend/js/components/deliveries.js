import { apiFetch } from '../api.js';
import { auth } from '../auth.js';

export async function renderDeliveries(container) {
  const farmId = localStorage.getItem('fw_selected_farm');
  if (!farmId || farmId === 'all') {
    container.innerHTML = `<div style="padding: 2rem; color: var(--danger);">Please select a farm first.</div>`;
    return;
  }

  container.innerHTML = `
    <div style="padding: 2rem; max-width: 1000px; margin: 0 auto;">
      <h2 style="margin-bottom: 1rem; color: var(--text-primary); font-size: 1.5rem; font-weight: 600;">🧾 出货对账 (Deliveries)</h2>
      <div id="deliveries-table-container">
        <div style="text-align: center; color: var(--text-secondary); padding: 2rem;">Loading...</div>
      </div>
    </div>
  `;

  await loadDeliveries(farmId);
}

async function loadDeliveries(farmId) {
  const tableContainer = document.getElementById('deliveries-table-container');
  try {
    const records = await apiFetch(`/deliveries/${farmId}`);
    
    if (!records || records.length === 0) {
      tableContainer.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--text-secondary); background:var(--surface-color); border-radius:0.5rem; box-shadow:0 1px 3px rgba(0,0,0,0.1);">没有出货记录。 (No delivery records found)</div>`;
      return;
    }

    let html = `
      <div style="overflow-x: auto; background: var(--surface-color); border-radius: 0.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <table style="width: 100%; border-collapse: collapse; min-width: 800px;">
          <thead>
            <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
              <th style="padding: 1rem;">时间 (Date)</th>
              <th style="padding: 1rem;">单据 (Receipt)</th>
              <th style="padding: 1rem;">出货重量 (Weight)</th>
              <th style="padding: 1rem;">篮子出/回 (Baskets Out/In)</th>
              <th style="padding: 1rem;">状态 (Status)</th>
              <th style="padding: 1rem;">操作 (Action)</th>
            </tr>
          </thead>
          <tbody>
    `;

    records.forEach(record => {
      const dateStr = new Date(record.created_at).toLocaleString();
      const statusBadge = record.is_reconciled 
        ? `<span style="background: var(--success); color: white; padding: 0.25rem 0.5rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">已核对 (Reconciled)</span>`
        : `<span style="background: var(--warning); color: white; padding: 0.25rem 0.5rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600;">待核对 (Pending)</span>`;
      
      const actionBtn = record.is_reconciled
        ? `<button disabled style="background: #e2e8f0; color: #94a3b8; padding: 0.5rem 1rem; border-radius: 0.25rem; border: none; cursor: not-allowed; font-weight:600;">✅ 完成</button>`
        : `<button class="btn btn-primary reconcile-btn" data-id="${record.id}" style="padding: 0.5rem 1rem; border-radius: 0.25rem; border: none; cursor: pointer; font-weight:600;">✅ 标记核对</button>`;

      const photoHtml = record.photo_thumbnail 
        ? `<a href="${record.photo_url}" target="_blank"><img src="${record.photo_thumbnail}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 0.25rem; border: 1px solid var(--border-color);" alt="receipt"></a>`
        : `<div style="width: 60px; height: 60px; background: #e2e8f0; display:flex; align-items:center; justify-content:center; border-radius:0.25rem; color:#94a3b8; font-size:0.75rem;">无照片</div>`;

      html += `
        <tr style="border-bottom: 1px solid var(--border-color);">
          <td style="padding: 1rem; color: var(--text-secondary); font-size: 0.875rem;">${dateStr}</td>
          <td style="padding: 1rem;">${photoHtml}</td>
          <td style="padding: 1rem; font-weight: 700; color: var(--text-primary); font-size: 1.125rem;">${record.total_weight_kg} kg</td>
          <td style="padding: 1rem; color: var(--text-secondary);">
            出: <span style="font-weight:600; color:var(--danger);">${record.baskets_out}</span> <br/>
            回: <span style="font-weight:600; color:var(--success);">${record.baskets_in}</span>
          </td>
          <td style="padding: 1rem;">${statusBadge}</td>
          <td style="padding: 1rem;">${actionBtn}</td>
        </tr>
      `;
    });

    html += `
          </tbody>
        </table>
      </div>
    `;

    tableContainer.innerHTML = html;

    // Attach event listeners
    document.querySelectorAll('.reconcile-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const id = e.target.getAttribute('data-id');
        if (confirm('确认账目无误，标记为已核对？ (Confirm reconciled?)')) {
          try {
            await apiFetch(`/deliveries/${id}/reconcile`, { method: 'PUT' });
            await loadDeliveries(farmId);
          } catch(err) {
            alert('Error: ' + err.message);
          }
        }
      });
    });

  } catch (err) {
    tableContainer.innerHTML = `<div style="color:var(--danger); padding:2rem; text-align:center;">Failed to load deliveries data: ${err.message}</div>`;
  }
}
