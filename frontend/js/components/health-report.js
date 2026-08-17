import { api } from '../api.js';
import { t } from '../i18n.js';
import { auth } from '../auth.js';

export async function renderHealthReport(container) {
  const user = auth.getUser();
  
  // Show loading
  container.innerHTML = `
    <div class="page-container">
      <div class="glass-panel" style="text-align: center; padding: 3rem;">
        <div class="spinner"></div>
        <p>${t('common.loading') || 'Loading...'}</p>
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

    const photos = await api.photos.list(params);
    
    // Calculate stats
    const stats = {
      healthy: photos.filter(p => p.health_status === 'healthy').length,
      warning: photos.filter(p => p.health_status === 'warning').length,
      critical: photos.filter(p => p.health_status === 'critical').length,
      pending: photos.filter(p => p.health_status === 'pending').length
    };
    const total = photos.length;

    // Helper for percentage
    const percent = (val) => total > 0 ? Math.round((val / total) * 100) : 0;

    container.innerHTML = `
      <div class="page-container" style="animation: fadeIn 0.5s ease-out;">
        
        <div class="health-dashboard">
          <div class="health-card glass-panel healthy-bg fade-in" style="animation-delay: 0.1s">
            <div class="health-icon">🌱</div>
            <div class="health-title">Healthy</div>
            <div class="health-count">${stats.healthy}</div>
            <div class="health-percent">${percent(stats.healthy)}% of crops</div>
          </div>
          
          <div class="health-card glass-panel warning-bg fade-in" style="animation-delay: 0.2s">
            <div class="health-icon">⚠️</div>
            <div class="health-title">Warning</div>
            <div class="health-count">${stats.warning}</div>
            <div class="health-percent">${percent(stats.warning)}% of crops</div>
          </div>
          
          <div class="health-card glass-panel critical-bg fade-in" style="animation-delay: 0.3s">
            <div class="health-icon">🚨</div>
            <div class="health-title">Critical</div>
            <div class="health-count">${stats.critical}</div>
            <div class="health-percent">${percent(stats.critical)}% of crops</div>
          </div>
        </div>

        <div class="glass-panel fade-in" style="margin-top: 2rem; animation-delay: 0.4s">
          <h3 style="margin-bottom: 1.5rem; color: var(--primary);">Attention Required</h3>
          <div class="attention-list">
            ${photos.filter(p => p.health_status === 'critical' || p.health_status === 'warning').map(p => {
              const aiData = p.ai_analysis ? JSON.parse(p.ai_analysis) : null;
              return `
                <div class="attention-item ${p.health_status}">
                  <img src="${p.thumbnail_path}" alt="crop" class="attention-img" />
                  <div class="attention-info">
                    <h4>${p.farm_name}</h4>
                    <p>${aiData ? aiData.notes : 'No AI notes'}</p>
                    <span class="badge badge-${p.health_status}">${p.health_status}</span>
                    <span class="text-secondary" style="font-size: 0.8rem; margin-left: 0.5rem;">${new Date(p.captured_at).toLocaleDateString()}</span>
                  </div>
                </div>
              `;
            }).join('') || '<p class="text-secondary">No current issues requiring attention. Great job!</p>'}
          </div>
        </div>

        <div class="glass-panel fade-in" style="margin-top: 2rem; animation-delay: 0.5s">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <h3 style="color: var(--primary); margin:0;">💰 财务预算与肥料需求 (Fertilizer Budget)</h3>
            <select id="budget-month-select" class="form-input" style="padding: 0.5rem; border-radius: var(--radius-sm);">
                <option value="1">1月 (Jan)</option>
                <option value="2">2月 (Feb)</option>
                <option value="3">3月 (Mar)</option>
                <option value="4">4月 (Apr)</option>
                <option value="5">5月 (May)</option>
                <option value="6">6月 (Jun)</option>
                <option value="7">7月 (Jul)</option>
                <option value="8">8月 (Aug)</option>
                <option value="9">9月 (Sep)</option>
                <option value="10">10月 (Oct)</option>
                <option value="11">11月 (Nov)</option>
                <option value="12">12月 (Dec)</option>
            </select>
          </div>
          <div id="budget-content">
            <div class="text-center text-secondary">载入中 (Loading)...</div>
          </div>
        </div>

      </div>
      
      <style>
        .health-dashboard {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 1.5rem;
        }
        .health-card {
          padding: 2rem;
          text-align: center;
          border-top: 4px solid transparent;
          transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        .health-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        }
        .healthy-bg { border-top-color: var(--success); }
        .warning-bg { border-top-color: var(--warning); }
        .critical-bg { border-top-color: var(--danger); }
        
        .health-icon { font-size: 3rem; margin-bottom: 1rem; }
        .health-title { font-size: 1.2rem; font-weight: 600; color: var(--text-secondary); }
        .health-count { font-size: 3rem; font-weight: 700; color: var(--primary-dark); margin: 0.5rem 0; }
        .health-percent { font-size: 0.9rem; color: var(--text-secondary); }
        
        .attention-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        .attention-item {
          display: flex;
          align-items: center;
          gap: 1.5rem;
          padding: 1rem;
          border-radius: var(--radius);
          background: rgba(255, 255, 255, 0.5);
          border-left: 4px solid transparent;
          transition: background 0.2s;
        }
        .attention-item:hover { background: rgba(255, 255, 255, 0.8); }
        .attention-item.warning { border-left-color: var(--warning); }
        .attention-item.critical { border-left-color: var(--danger); }
        .attention-img {
          width: 80px;
          height: 80px;
          border-radius: var(--radius);
          object-fit: cover;
        }
        .attention-info h4 { margin: 0 0 0.5rem 0; color: var(--primary); }
        .attention-info p { margin: 0 0 0.5rem 0; color: var(--text-primary); font-size: 0.95rem; }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .fade-in {
          animation: fadeIn 0.6s ease-out backwards;
        }
      </style>
    `;

    const budgetMonthSelect = document.getElementById('budget-month-select');
    const budgetContent = document.getElementById('budget-content');
    
    // Set current month as default
    const currentMonth = new Date().getMonth() + 1;
    if(budgetMonthSelect) budgetMonthSelect.value = currentMonth;
    
    const loadBudget = async (month) => {
        if(!budgetContent) return;
        budgetContent.innerHTML = '<div class="text-center text-secondary">载入中 (Loading)...</div>';
        try {
            const budgetData = await api.reports.fertilizerBudget(params.farm_id, month);
            if (!budgetData.items || budgetData.items.length === 0) {
                budgetContent.innerHTML = '<div class="text-center text-secondary" style="padding: 1rem;">此月份无肥料需求排程。</div>';
                return;
            }
            
            let html = `
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 1rem;">
                    <thead>
                        <tr style="border-bottom: 2px solid var(--border-color); text-align: left;">
                            <th style="padding: 0.8rem; color: var(--text-secondary);">肥料名称</th>
                            <th style="padding: 0.8rem; color: var(--text-secondary);">需求数量</th>
                            <th style="padding: 0.8rem; color: var(--text-secondary);">单价 (RM)</th>
                            <th style="padding: 0.8rem; color: var(--text-secondary);">预估花费 (RM)</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            budgetData.items.forEach(item => {
                html += `
                    <tr style="border-bottom: 1px solid var(--border-color);">
                        <td style="padding: 0.8rem; font-weight: 500;">${item.name}</td>
                        <td style="padding: 0.8rem;">${item.quantity} ${item.unit}</td>
                        <td style="padding: 0.8rem;">${item.cost_per_unit.toFixed(2)}</td>
                        <td style="padding: 0.8rem; font-weight: 600; color: var(--danger);">${item.total_cost.toFixed(2)}</td>
                    </tr>
                `;
            });
            
            html += `
                    </tbody>
                </table>
                <div style="text-align: right; padding: 1rem; background: rgba(0,0,0,0.02); border-radius: var(--radius-sm);">
                    <span style="font-size: 1.2rem; color: var(--text-secondary);">本月总预算: </span>
                    <span style="font-size: 1.5rem; font-weight: 700; color: var(--primary);">RM ${budgetData.total_budget.toFixed(2)}</span>
                </div>
            `;
            
            budgetContent.innerHTML = html;
        } catch(e) {
            budgetContent.innerHTML = '<div class="text-danger text-center">载入失败</div>';
        }
    };
    
    if (params.farm_id && budgetMonthSelect) {
        await loadBudget(currentMonth);
        budgetMonthSelect.addEventListener('change', (e) => {
            loadBudget(e.target.value);
        });
    }

  } catch (err) {
    console.error('Failed to load health report:', err);
    container.innerHTML = `<div class="page-container"><p style="color:var(--danger)">Error loading health report.</p></div>`;
  }
}
