import sys

with open('frontend/js/components/health-report.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Let's find where to insert the new HTML section.
# We will insert it right after the "Attention Required" section block.
target = '''          </div>
        </div>
      </div>
      
      <style>'''

new_section = '''          </div>
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
      
      <style>'''

content = content.replace(target, new_section)

# Now inject the JavaScript to load the budget
target_js = '''  } catch (err) {
    console.error('Failed to load health report:', err);'''

new_js = '''
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
    console.error('Failed to load health report:', err);'''

content = content.replace(target_js, new_js)

with open('frontend/js/components/health-report.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated health-report.js")
