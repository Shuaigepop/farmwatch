import { t } from '../i18n.js';
import { api } from '../api.js';

export async function renderPhotoWall(container) {
  container.innerHTML = `
    <div class="page-container slide-in">
      <h2 style="margin-bottom: 1.5rem;">${t('photos.title')}</h2>
      
      <div class="filter-bar">
        <select class="form-input" style="width: 200px;" id="photo-status-filter">
          <option value="">${t('photos.statusFilter')}</option>
          <option value="healthy">${t('health.healthy')}</option>
          <option value="warning">${t('health.warning')}</option>
          <option value="critical">${t('health.critical')}</option>
        </select>
        <button class="btn btn-primary" id="photo-filter-btn">${t('common.filter')}</button>
      </div>

      <div class="photo-grid" id="photo-grid-content">
        <!-- Skeletons while loading -->
        <div class="photo-card skeleton"><div class="skeleton-img"></div></div>
        <div class="photo-card skeleton"><div class="skeleton-img"></div></div>
        <div class="photo-card skeleton"><div class="skeleton-img"></div></div>
      </div>
    </div>

    <!-- Lightbox -->
    <div class="lightbox" id="photo-lightbox">
      <button class="close-btn" id="lightbox-close">×</button>
      <div class="lightbox-content">
        <div class="lightbox-img-container">
          <img src="" class="lightbox-img" id="lightbox-img-el">
        </div>
        <div class="lightbox-sidebar">
          <h3 id="lb-farm-name">Farm Name</h3>
          
          <div>
            <div class="text-sm text-secondary">${t('photos.uploadedBy')}</div>
            <div class="font-semibold" id="lb-uploader">Uploader</div>
            <div class="text-sm text-secondary" style="margin-top:0.2rem;" id="lb-date">Date</div>
          </div>
          
          <div style="margin-top: 1rem;">
            <div class="text-sm text-secondary mb-2">Status</div>
            <span class="tag tag-healthy" id="lb-status">Healthy</span>
          </div>
          
          <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border-color);">
            <div class="text-sm text-secondary" style="margin-bottom: 0.5rem;">${t('photos.aiAnalysis')} 🤖</div>
            <p class="text-sm" id="lb-ai-notes">Notes here...</p>
          </div>
        </div>
      </div>
    </div>
  `;

  const grid = document.getElementById('photo-grid-content');
  
  const params = {};
  const globalFarmSelect = document.getElementById('global-farm-select');
  if (globalFarmSelect && globalFarmSelect.value !== 'all') {
    params.farm_id = parseInt(globalFarmSelect.value);
  }

  let photos = await api.photos.list(params);

  if (!photos.length) {
    grid.innerHTML = `<div class="text-secondary">${t('common.noData')}</div>`;
    return;
  }

  const getStatusTag = (status) => {
    return `<span class="tag tag-${status}">${t(`health.${status}`)}</span>`;
  };

  grid.innerHTML = photos.map(p => {
    let imgUrl = p.thumbnail_path || p.file_path;
    if (imgUrl && !imgUrl.startsWith('http')) {
      imgUrl = `/api/photos/uploads/${imgUrl}`;
    }
    const farmName = p.farm_name || (p.farm_id ? `農場 ${p.farm_id}` : '未指定農場');
    const dateStr = p.captured_at ? new Date(p.captured_at).toLocaleDateString() : '';
    const uploader = p.uploader || '員工';
    const status = p.health_status || 'pending';
    
    return `
      <div class="photo-card" data-id="${p.id}">
        <img src="${imgUrl}" class="photo-img" loading="lazy">
        <div class="photo-info">
          <div class="photo-meta">
            <span class="font-semibold">${farmName}</span>
            <span>${dateStr}</span>
          </div>
          <div class="flex justify-between items-center" style="margin-top: 0.5rem;">
            <span class="text-sm text-secondary">${uploader}</span>
            ${getStatusTag(status)}
          </div>
        </div>
      </div>
    `;
  }).join('');

  document.getElementById('photo-filter-btn').addEventListener('click', async () => {
    const statusVal = document.getElementById('photo-status-filter').value;
    const filterParams = { ...params };
    if (statusVal) filterParams.health_status = statusVal;
    
    grid.innerHTML = '<div class="spinner"></div>';
    photos = await api.photos.list(filterParams);
    renderPhotoWallGrid(grid, photos);
  });

  function renderPhotoWallGrid(container, photoList) {
    if (!photoList.length) {
      container.innerHTML = `<div class="text-secondary">${t('common.noData')}</div>`;
      return;
    }
    container.innerHTML = photoList.map(p => {
      let imgUrl = p.thumbnail_path || p.file_path;
      if (imgUrl && !imgUrl.startsWith('http')) {
        imgUrl = `/api/photos/uploads/${imgUrl}`;
      }
      const farmName = p.farm_name || (p.farm_id ? `农场 ${p.farm_id}` : '未指定农场');
      const dateStr = p.captured_at ? new Date(p.captured_at).toLocaleDateString() : '';
      const uploader = p.uploader || '员工';
      const status = p.health_status || 'pending';
      return `
        <div class="photo-card" data-id="${p.id}">
          <img src="${imgUrl}" class="photo-img" loading="lazy">
          <div class="photo-info">
            <div class="photo-meta">
              <span class="font-semibold">${farmName}</span>
              <span>${dateStr}</span>
            </div>
            <div class="flex justify-between items-center" style="margin-top: 0.5rem;">
              <span class="text-sm text-secondary">${uploader}</span>
              <span class="tag tag-${status}">${t(`health.${status}`)}</span>
            </div>
          </div>
        </div>
      `;
    }).join('');
    attachLightboxListeners();
  }

  function attachLightboxListeners() {
    document.querySelectorAll('.photo-card').forEach(card => {
      card.addEventListener('click', async () => {
        const id = card.dataset.id;
        const p = photos.find(x => x.id == id);
        if (!p) return;
        
        let imgUrl = p.file_path;
        if (imgUrl && !imgUrl.startsWith('http')) {
          imgUrl = `/api/photos/uploads/${imgUrl}`;
        }
        
        document.getElementById('lightbox-img-el').src = imgUrl;
        document.getElementById('lb-farm-name').textContent = p.farm_name || (p.farm_id ? `农场 ${p.farm_id}` : '未指定农场');
        document.getElementById('lb-uploader').textContent = p.uploader || '员工';
        document.getElementById('lb-date').textContent = p.captured_at ? new Date(p.captured_at).toLocaleString() : '';
        
        const status = p.health_status || 'pending';
        document.getElementById('lb-status').className = `tag tag-${status}`;
        document.getElementById('lb-status').textContent = t(`health.${status}`);
        
        let aiNotes = '';
        if (p.ai_analysis) {
          try {
            const analysis = JSON.parse(p.ai_analysis);
            aiNotes = analysis.notes || p.ai_analysis;
          } catch(e) {
            aiNotes = p.ai_analysis;
          }
        } else {
          aiNotes = '待分析...';
        }
        document.getElementById('lb-ai-notes').textContent = aiNotes;
        
        document.getElementById('photo-lightbox').classList.add('active');
      });
    });
  }

  // Lightbox close logic
  const closeBtn = document.getElementById('lightbox-close');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      document.getElementById('photo-lightbox').classList.remove('active');
    });
  }
  
  renderPhotoWallGrid(grid, photos);
}
