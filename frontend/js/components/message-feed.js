import { t } from '../i18n.js';
import { api } from '../api.js';

export async function renderMessages(container) {
  container.innerHTML = `
    <div class="page-container slide-in" style="height: 100%; display: flex; flex-direction: column;">
      <h2 style="margin-bottom: 1.5rem;">${t('messages.title')}</h2>
      
      <div class="message-container">
        <div class="message-feed" id="chat-feed">
          <div class="text-center">
            <button class="btn" style="background: transparent; color: var(--primary); border: 1px solid var(--primary);">${t('messages.loadMore')}</button>
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
  const params = {};
  const globalFarmSelect = document.getElementById('global-farm-select');
  if (globalFarmSelect && globalFarmSelect.value !== 'all') {
    params.farm_id = parseInt(globalFarmSelect.value);
  }

  const messages = await api.messages.list(params);

  const renderMessage = (msg) => {
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

  messages.forEach(msg => {
    feed.insertAdjacentHTML('beforeend', renderMessage(msg));
  });
  
  feed.scrollTop = feed.scrollHeight;

  // Handle send
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    
    input.value = '';
    
    // Optimistic render
    const newMsg = await api.messages.send(text);
    feed.insertAdjacentHTML('beforeend', renderMessage(newMsg));
    feed.scrollTop = feed.scrollHeight;
  });
}
