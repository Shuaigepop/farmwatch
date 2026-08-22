import { t } from '../i18n.js';
import { api } from '../api.js';

export async function renderPhotoWall(container) {
  let currentOffset = 0;
  const LIMIT = 30;
  let allPhotos = [];
  let isLoading = false;
  let hasMore = true;
  
  // Set up params based on global selection
  const params = { limit: LIMIT };
  const globalFarmSelect = document.getElementById('global-farm-select');
  if (globalFarmSelect && globalFarmSelect.value !== 'all') {
    params.farm_id = parseInt(globalFarmSelect.value);
  }

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
        <!-- Grid Items Go Here -->
      </div>
      
      <!-- Loading indicator & Intersection Observer Target -->
      <div id="loading-target" style="text-align:center; padding: 2rem;">
        <div class="spinner" id="loading-spinner" style="display:none; margin: 0 auto;"></div>
        <p id="no-more-text" class="text-secondary" style="display:none; margin-top: 1rem;">到底了，沒有更多照片囉！</p>
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
  const spinner = document.getElementById('loading-spinner');
  const noMoreText = document.getElementById('no-more-text');

  const getStatusTag = (status) => {
    return `<span class="tag tag-${status}">${t(`health.${status}`)}</span>`;
  };

  const createPhotoCardHTML = (p) => {
    let imgUrl = p.thumbnail_path || p.file_path;
    if (imgUrl && !imgUrl.startsWith('http')) {
      imgUrl = `/api/photos/uploads/${imgUrl}`;
    }
    const farmName = p.farm_name || (p.farm_id ? `農場 ${p.farm_id}` : '未指定農場');
    const dateStr = p.captured_at ? new Date(p.captured_at).toLocaleDateString() : '';
    const uploader = p.uploader || '員工';
    const status = p.health_status || 'pending';
    
    return `
      <div class="photo-card fade-in" data-id="${p.id}">
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
  };

  // Attach click listener for Lightbox at the grid level (Event Delegation)
  grid.addEventListener('click', (e) => {
    const card = e.target.closest('.photo-card');
    if (!card) return;
    
    const id = card.dataset.id;
    const p = allPhotos.find(x => x.id == id);
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

  const loadPhotos = async (isReset = false) => {
    if (isLoading || (!hasMore && !isReset)) return;
    
    isLoading = true;
    spinner.style.display = 'block';
    if (isReset) {
      noMoreText.style.display = 'none';
    }

    try {
      const statusVal = document.getElementById('photo-status-filter').value;
      const fetchParams = { ...params, offset: currentOffset };
      if (statusVal) fetchParams.health_status = statusVal;

      const newPhotos = await api.photos.list(fetchParams);
      
      if (isReset) {
        grid.innerHTML = '';
        allPhotos = [];
      }

      if (newPhotos.length < LIMIT) {
        hasMore = false;
      }

      if (newPhotos.length > 0) {
        allPhotos.push(...newPhotos);
        const html = newPhotos.map(createPhotoCardHTML).join('');
        grid.insertAdjacentHTML('beforeend', html);
      } else if (isReset) {
        grid.innerHTML = `<div class="text-secondary" style="grid-column: 1 / -1; text-align: center;">${t('common.noData')}</div>`;
      }
      
      if (!hasMore && allPhotos.length > 0) {
         noMoreText.style.display = 'block';
      }
      
      currentOffset += LIMIT;

    } catch(err) {
      console.error('Error loading photos:', err);
    } finally {
      isLoading = false;
      spinner.style.display = 'none';
    }
  };

  // Setup Intersection Observer for infinite scrolling
  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      loadPhotos();
    }
  }, { rootMargin: '100px' });
  
  observer.observe(document.getElementById('loading-target'));

  // Filter Button
  document.getElementById('photo-filter-btn').addEventListener('click', () => {
    currentOffset = 0;
    hasMore = true;
    grid.innerHTML = '';
    loadPhotos(true);
  });

  // Lightbox close logic
  const closeBtn = document.getElementById('lightbox-close');
  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      document.getElementById('photo-lightbox').classList.remove('active');
    });
  }
}
