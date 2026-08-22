import { t } from '../i18n.js';
import { api, showToast } from '../api.js';

export async function renderMessages(container) {
  let currentOffset = 0;
  const LIMIT = 30;
  let allMessages = [];
  let isLoading = false;
  let hasMore = true;

  const params = { limit: LIMIT };
  const globalFarmSelect = document.getElementById('global-farm-select');
  if (globalFarmSelect && globalFarmSelect.value !== 'all') {
    params.farm_id = parseInt(globalFarmSelect.value);
  }

  container.innerHTML = `
    <div class="page-container slide-in" style="height: 100%; display: flex; flex-direction: column;">
      <h2 style="margin-bottom: 1.5rem;">${t('messages.title')}</h2>
      
      <div class="message-container">
        <div class="message-feed" id="chat-feed" style="overflow-y: auto;">
          <div id="load-more-container" class="text-center" style="padding: 1rem 0;">
            <button id="load-more-btn" class="btn" style="background: transparent; color: var(--primary); border: 1px solid var(--primary); display:none;">${t('messages.loadMore')}</button>
            <div class="spinner" id="chat-spinner" style="display:none; margin: 0 auto;"></div>
          </div>
          <!-- Messages will be injected here -->
        </div>
        
        <form class="message-input-area" id="chat-form">
          <input type="text" class="msg-input" id="chat-input" placeholder="${t('messages.typeMessage')}" required autocomplete="off">
          <button type="submit" class="btn btn-primary" style="width: auto; border-radius: var(--radius-full); padding: 0.75rem 2rem;">
            ${t('common.send')} ↗
          </button>
        </form>
      </div>
    </div>
  `;

  const feed = document.getElementById('chat-feed');
  const loadMoreContainer = document.getElementById('load-more-container');
  const loadMoreBtn = document.getElementById('load-more-btn');
  const spinner = document.getElementById('chat-spinner');

  const renderMessageHTML = (msg) => {
    const isOwn = msg.is_reply;
    const senderName = msg.line_user_name || '員工';
    const initial = senderName.charAt(0);
    const time = new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    let contentHtml = '';
    if (msg.message_type === 'image' && msg.image_url) {
      contentHtml = `<img src="${msg.image_url}" alt="Photo" style="max-width: 100%; border-radius: var(--radius-md); margin-top: 0.5rem;" />`;
    } else {
      contentHtml = `<div class="message-text">${msg.content || ''}</div>`;
    }

    return `
      <div class="message ${isOwn ? 'own' : 'slide-in'}">
        <div class="message-avatar">${initial}</div>
        <div class="message-content">
          <div class="message-header">
            <span class="message-sender">${senderName}</span>
            <span class="message-time">${time}</span>
          </div>
          ${contentHtml}
        </div>
      </div>
    `;
  };

  const loadMessages = async (isInitial = false) => {
    if (isLoading || !hasMore) return;
    isLoading = true;
    
    loadMoreBtn.style.display = 'none';
    spinner.style.display = 'block';

    try {
      const fetchParams = { ...params, offset: currentOffset };
      const newMessages = await api.messages.list(fetchParams);
      
      if (newMessages.length < LIMIT) {
        hasMore = false;
      }

      if (newMessages.length > 0) {
        // Backend returns newest first. We reverse to oldest first for display
        const displayMessages = [...newMessages].reverse();
        allMessages.unshift(...displayMessages); // keep track in memory if needed
        
        const html = displayMessages.map(renderMessageHTML).join('');
        
        if (isInitial) {
           loadMoreContainer.insertAdjacentHTML('afterend', html);
           // Scroll to bottom on initial load
           feed.scrollTop = feed.scrollHeight;
        } else {
           // Save scroll position before prepending
           const previousHeight = feed.scrollHeight;
           loadMoreContainer.insertAdjacentHTML('afterend', html);
           feed.scrollTop = feed.scrollHeight - previousHeight;
        }
      }
      
      currentOffset += LIMIT;
      
    } catch (err) {
      console.error('Error loading messages', err);
    } finally {
      isLoading = false;
      spinner.style.display = 'none';
      if (hasMore) {
        loadMoreBtn.style.display = 'inline-block';
      }
    }
  };

  loadMoreBtn.addEventListener('click', () => {
    loadMessages(false);
  });

  // Initial load
  await loadMessages(true);

  // Handle send
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    
    input.value = '';
    
    if (!params.farm_id) {
       showToast('❌ Please select a farm first', 'error');
       return;
    }

    try {
      // Optimitic UI can be tricky if we don't know the ID, but backend returns success.
      // Wait for backend to return the created message? 
      // api.messages.send doesn't return the full message in the real API, it returns {"status": "success"}
      // Let's just reload the feed or prepend a fake message.
      await api.messages.send({ farm_id: params.farm_id, content: text });
      
      // Real app might fetch just the newest message, but for simplicity, we insert a local fake message
      const fakeMsg = {
        is_reply: true,
        line_user_name: 'Me',
        created_at: new Date().toISOString(),
        message_type: 'text',
        content: text
      };
      
      feed.insertAdjacentHTML('beforeend', renderMessageHTML(fakeMsg));
      feed.scrollTop = feed.scrollHeight;
      
    } catch(err) {
      showToast('❌ Failed to send message', 'error');
    }
  });
}
