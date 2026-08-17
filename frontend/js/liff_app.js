const API_BASE = '/api';

// Tab Switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        
        // Add active class to clicked
        btn.classList.add('active');
        const target = btn.getAttribute('data-tab');
        document.getElementById(`tab-${target}`).classList.add('active');
    });
});

// App State
let lineUserId = null;
let currentFarmId = 6; // Hardcoded for demo/worker fallback

async function initLiff() {
    try {
        // Initialize LIFF (Requires your actual LIFF ID here eventually)
        // await liff.init({ liffId: "YOUR_LIFF_ID" });
        // if (liff.isLoggedIn()) {
        //     const profile = await liff.getProfile();
        //     lineUserId = profile.userId;
        //     document.getElementById('profile-name').innerText = profile.displayName;
        // } else {
        //     liff.login();
        // }
        
        // Mock profile for now
        document.getElementById('profile-name').innerText = "Worker (Testing)";
        
        // Load Data
        loadZones();
        loadInventory();
        
    } catch (err) {
        console.error('LIFF init failed', err);
        document.getElementById('profile-name').innerText = "Load Error";
    }
}

async function loadZones() {
    try {
        const res = await fetch(`${API_BASE}/farms/${currentFarmId}/zones`);
        if (res.ok) {
            const zones = await res.json();
            const select = document.getElementById('task-zones');
            select.innerHTML = '<option value="">Select Zone...</option>';
            zones.forEach(z => {
                select.innerHTML += `<option value="${z.id}">${z.name}</option>`;
            });
            
            // Add event listener to load tasks when zone changes
            select.addEventListener('change', (e) => loadTasksForZone(e.target.value));
        }
    } catch (err) {
        console.error('Failed to load zones', err);
    }
}

async function loadTasksForZone(zoneId) {
    const taskSelect = document.getElementById('task-list');
    if (!zoneId) {
        taskSelect.innerHTML = '<option value="">Select a zone first...</option>';
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/tasks/?farm_id=${currentFarmId}`);
        if (res.ok) {
            const allTasks = await res.json();
            const zoneTasks = allTasks.filter(t => t.zone_id == zoneId && t.status !== 'completed');
            
            taskSelect.innerHTML = '<option value="">Select Task...</option>';
            zoneTasks.forEach(t => {
                taskSelect.innerHTML += `<option value="${t.id}">${t.title}</option>`;
            });
        }
    } catch (err) {
        console.error('Failed to load tasks', err);
    }
}

async function loadInventory() {
    try {
        // Fetch inventory (using deliveries trick or direct if exists)
        // Since we don't have a direct inventory list API, I'll mock it based on what exists, or just use a generic list
        // Wait, we do have /api/deliveries but wait we need supplies. Let's assume standard names for now
        const items = [
            {id: 1, name: '肥料 A (Fertilizer A)'},
            {id: 2, name: '农药 B (Pesticide B)'},
            {id: 3, name: '空篮子 (Kosong)'}
        ];
        
        const select = document.getElementById('supply-items');
        select.innerHTML = '<option value="">Select Item...</option>';
        items.forEach(i => {
            select.innerHTML += `<option value="${i.id}">${i.name}</option>`;
        });
    } catch (err) {
        console.error('Failed to load inventory', err);
    }
}

// Form Submissions
function showLoader() { document.getElementById('loader').classList.remove('hidden'); }
function hideLoader() { document.getElementById('loader').classList.add('hidden'); }

async function submitForm(url, payload) {
    showLoader();
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (res.ok) {
            alert('✅ Success! (Berjaya! / ပြီးပါပြီ!)');
            // If in LINE app, close the window
            if (typeof liff !== 'undefined' && liff.isInClient()) {
                liff.closeWindow();
            }
        } else {
            alert('❌ Failed to submit.');
        }
    } catch (err) {
        console.error(err);
        alert('❌ Error occurred.');
    } finally {
        hideLoader();
    }
}

document.getElementById('form-delivery').addEventListener('submit', (e) => {
    e.preventDefault();
    const payload = {
        action: 'delivery',
        farm_id: currentFarmId,
        line_user_id: lineUserId,
        weight: parseFloat(e.target.weight.value),
        baskets_out: parseInt(e.target.baskets_out.value),
        baskets_in: parseInt(e.target.baskets_in.value)
    };
    submitForm(`${API_BASE}/liff/submit`, payload);
});

document.getElementById('form-supply').addEventListener('submit', (e) => {
    e.preventDefault();
    const payload = {
        action: 'supply',
        farm_id: currentFarmId,
        line_user_id: lineUserId,
        item_id: parseInt(e.target.item_id.value),
        quantity: parseFloat(e.target.quantity.value)
    };
    submitForm(`${API_BASE}/liff/submit`, payload);
});

document.getElementById('form-task').addEventListener('submit', (e) => {
    e.preventDefault();
    const payload = {
        action: 'task',
        farm_id: currentFarmId,
        line_user_id: lineUserId,
        task_id: parseInt(e.target.task_id.value)
    };
    submitForm(`${API_BASE}/liff/submit`, payload);
});

// Start
initLiff();
