import { api } from '../api.js';
import { t } from '../i18n.js';
import { auth } from '../auth.js';

export async function renderDailySummary(container) {
  const user = auth.getUser();
  
  // Set default date to today in YYYY-MM-DD
  const today = new Date().toISOString().split('T')[0];
  let targetDate = today;

  const renderContent = async () => {
    container.innerHTML = `
      <div class="page-container">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 2rem;">
          <div>
            <h2 style="margin: 0; color: var(--primary-dark);">Daily Summary (日报)</h2>
            <p class="text-secondary" style="margin: 0;">AI Farm Diary & Overview</p>
          </div>
          <div>
             <input type="date" id="summary-date-picker" value="${targetDate}" class="form-input" style="padding: 0.5rem; font-size:1.1rem; border-radius: var(--radius-sm); border: 1px solid var(--primary);">
          </div>
        </div>
        <div class="glass-panel" style="text-align: center; padding: 3rem;">
          <div class="spinner"></div>
        </div>
      </div>
    `;

    document.getElementById('summary-date-picker').addEventListener('change', (e) => {
      targetDate = e.target.value;
      renderContent();
    });

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

      // Fetch Tasks
      const token = localStorage.getItem('fw_token');
      const fetchJson = async (url) => {
        const res = await fetch(url, { headers: { 'Authorization': 'Bearer ' + token } });
        if(!res.ok) throw new Error('API Error');
        return res.json();
      };

      const tasks = await fetchJson(`/api/tasks/?farm_id=${farmId}&target_date=${targetDate}`);
      const photos = await fetchJson(`/api/photos/?farm_id=${farmId}&target_date=${targetDate}`);
      const reports = await fetchJson(`/api/reports/daily?farm_id=${farmId}&target_date=${targetDate}`);
      const report = reports.length > 0 ? reports[0] : null;

      // Calculate task stats
      const totalTasks = tasks.length;
      const completedTasks = tasks.filter(t => t.status === 'completed');
      const pendingTasks = tasks.filter(t => t.status !== 'completed');
      const completionRate = totalTasks > 0 ? Math.round((completedTasks.length / totalTasks) * 100) : 0;
      
      let aiText = "当天尚无 AI 总结。";
      if (report) {
         try {
           const parsed = JSON.parse(report.summary_json);
           aiText = parsed.text || report.summary_json;
         } catch(e) {
           aiText = report.summary_json;
         }
      }

      const contentHTML = `
        <div class="page-container slide-in">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 2rem;">
            <div>
              <h2 style="margin: 0; color: var(--primary-dark);">Daily Summary (日报)</h2>
              <p class="text-secondary" style="margin: 0;">AI Farm Diary & Overview</p>
            </div>
            <div>
               <input type="date" id="summary-date-picker-loaded" value="${targetDate}" class="form-input" style="padding: 0.5rem; font-size:1.1rem; border-radius: var(--radius-sm); border: 1px solid var(--primary);">
            </div>
          </div>

          <!-- Section 1: Task Stats -->
          <h3 style="margin-bottom: 1rem; border-bottom: 2px solid var(--border-color); padding-bottom: 0.5rem;">📊 工作达成率 (Task Completion)</h3>
          <div class="glass-panel" style="padding: 1.5rem; margin-bottom: 2rem;">
            <div style="display:flex; align-items:center; gap: 1rem; margin-bottom: 1rem;">
              <div style="flex:1; background: rgba(0,0,0,0.05); height: 20px; border-radius: 10px; overflow:hidden;">
                <div style="width: ${completionRate}%; background: var(--success); height: 100%; transition: width 1s ease;"></div>
              </div>
              <div style="font-weight:bold; color:var(--success); font-size:1.2rem;">${completionRate}%</div>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
              <div style="background: rgba(40,167,69,0.05); padding: 1rem; border-radius: var(--radius-sm);">
                <h4 style="color:var(--success); margin-top:0;">已完成 (${completedTasks.length})</h4>
                <ul style="padding-left:1.2rem; margin:0; color:var(--text-secondary); font-size:0.9rem;">
                  ${completedTasks.map(t => `<li style="margin-bottom:0.3rem;">${t.title}</li>`).join('') || '<li>无</li>'}
                </ul>
              </div>
              <div style="background: rgba(255,193,7,0.05); padding: 1rem; border-radius: var(--radius-sm);">
                <h4 style="color:var(--warning); margin-top:0;">未完成 (${pendingTasks.length})</h4>
                <ul style="padding-left:1.2rem; margin:0; color:var(--text-secondary); font-size:0.9rem;">
                  ${pendingTasks.map(t => `<li style="margin-bottom:0.3rem;">${t.title}</li>`).join('') || '<li>无</li>'}
                </ul>
              </div>
            </div>
          </div>

          <!-- Section 2: Photos & Crop Health -->
          <h3 style="margin-bottom: 1rem; border-bottom: 2px solid var(--border-color); padding-bottom: 0.5rem;">📷 巡检照片与 AI 分析 (Photos & Analysis)</h3>
          <div class="reports-grid" style="margin-bottom: 2rem;">
            ${photos.length ? photos.map(p => {
              const fileName = p.thumbnail_path.split('/').pop().split('\\').pop();
              return `
              <div class="glass-panel fade-in" style="padding: 1rem; display:flex; gap: 1rem;">
                <img src="/api/photos/uploads/${fileName}" style="width: 120px; height: 120px; object-fit: cover; border-radius: var(--radius-sm);" alt="Farm Photo">
                <div style="flex: 1; display:flex; flex-direction:column;">
                   <span class="badge ${p.health_status === 'healthy' ? 'badge-success' : (p.health_status === 'warning' ? 'badge-warning' : 'badge-danger')}" style="align-self:flex-start; margin-bottom:0.5rem;">${p.health_status.toUpperCase()}</span>
                   <p class="text-sm text-secondary" style="margin:0; flex:1; overflow-y:auto; max-height:80px;">${p.ai_analysis || 'No AI analysis available.'}</p>
                   <span class="text-sm" style="color:var(--primary); margin-top:0.5rem;">${new Date(p.captured_at).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'})}</span>
                </div>
              </div>
              `;
            }).join('') : '<div class="glass-panel"><p class="text-secondary text-center" style="padding:1rem;">当日无巡检照片</p></div>'}
          </div>

          <!-- Section 3: AI Daily Report -->
          <h3 style="margin-bottom: 1rem; border-bottom: 2px solid var(--border-color); padding-bottom: 0.5rem;">🤖 大管家每日总结 (AI Daily Insights)</h3>
          <div class="glass-panel fade-in" style="padding: 2rem; border-left: 4px solid var(--primary); background: linear-gradient(135deg, rgba(255,255,255,0.8), rgba(255,255,255,0.4)); margin-bottom: 3rem;">
             ${report ? `
               <div style="white-space: pre-wrap; line-height: 1.8; color: var(--text-primary); font-size:1.05rem;">${aiText}</div>
               <div class="text-secondary text-sm" style="margin-top: 1.5rem; text-align:right;">Generated at ${new Date(report.created_at).toLocaleTimeString()}</div>
             ` : `
               <p class="text-secondary text-center" style="margin:0;">当日尚无 AI 总结。总结通常于晚上排程自动生成。</p>
             `}
          </div>

        </div>
        <style>
          .reports-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 1.5rem;
          }
          .fade-in { animation: fadeIn 0.5s ease-out backwards; }
          @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
          }
        </style>
      `;

      container.innerHTML = contentHTML;

      // Re-bind listener for the new date picker in loaded DOM
      document.getElementById('summary-date-picker-loaded').addEventListener('change', (e) => {
        targetDate = e.target.value;
        renderContent();
      });

    } catch (err) {
      console.error('Failed to load summary:', err);
      container.innerHTML = `
        <div class="page-container">
           <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 2rem;">
            <div>
              <h2 style="margin: 0; color: var(--primary-dark);">Daily Summary (日报)</h2>
            </div>
            <div>
               <input type="date" id="summary-date-picker-error" value="${targetDate}" class="form-input" style="padding: 0.5rem; font-size:1.1rem;">
            </div>
          </div>
          <p style="color:var(--danger)">Error loading daily summary.</p>
        </div>`;
      document.getElementById('summary-date-picker-error').addEventListener('change', (e) => {
        targetDate = e.target.value;
        renderContent();
      });
    }
  };

  // Initial load
  renderContent();
}
