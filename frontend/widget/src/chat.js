/**
 * Keystone AI Receptionist Chat Widget
 * Embeddable chat widget for self-care businesses
 */

(function() {
  'use strict';

  const WIDGET_VERSION = '1.0.0';
  
  const DEFAULT_API_URL = 'http://localhost:8001';
  
  class KeystoneChatWidget {
    constructor(config) {
      this.businessId = config.businessId;
      this.apiUrl = config.apiUrl || DEFAULT_API_URL;
      this.sessionId = this.getOrCreateSessionId();
      this.isOpen = false;
      this.isLoading = false;
      this.messages = [];
      
      this.init();
    }
    
    getOrCreateSessionId() {
      const storageKey = `keystone_session_${this.businessId}`;
      let sessionId = localStorage.getItem(storageKey);
      
      if (!sessionId) {
        sessionId = 'sess_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
        localStorage.setItem(storageKey, sessionId);
      }
      
      return sessionId;
    }
    
    async init() {
      this.injectStyles();
      this.createWidget();
      this.bindEvents();
      await this.loadHistory();
    }
    
    injectStyles() {
      if (document.getElementById('keystone-chat-styles')) return;
      
      const style = document.createElement('style');
      style.id = 'keystone-chat-styles';
      style.textContent = `/* AI Receptionist Chat Widget Styles */
.keystone-chat-widget {
  --keystone-primary: #6366f1;
  --keystone-primary-hover: #4f46e5;
  --keystone-bg: #ffffff;
  --keystone-text: #1f2937;
  --keystone-text-light: #6b7280;
  --keystone-border: #e5e7eb;
  --keystone-user-bg: #6366f1;
  --keystone-user-text: #ffffff;
  --keystone-bot-bg: #f3f4f6;
  --keystone-bot-text: #1f2937;
  --keystone-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  --keystone-radius: 16px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 99999;
}
.keystone-chat-toggle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--keystone-primary);
  border: none;
  cursor: pointer;
  box-shadow: var(--keystone-shadow);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}
.keystone-chat-toggle:hover { background: var(--keystone-primary-hover); transform: scale(1.05); }
.keystone-chat-toggle svg { width: 28px; height: 28px; fill: white; }
.keystone-chat-toggle.open .keystone-icon-chat { display: none; }
.keystone-chat-toggle:not(.open) .keystone-icon-close { display: none; }
.keystone-chat-container {
  position: absolute;
  bottom: 75px;
  right: 0;
  width: 380px;
  max-width: calc(100vw - 40px);
  height: 550px;
  max-height: calc(100vh - 120px);
  background: var(--keystone-bg);
  border-radius: var(--keystone-radius);
  box-shadow: var(--keystone-shadow);
  display: none;
  flex-direction: column;
  overflow: hidden;
  animation: keystone-slide-up 0.3s ease;
}
.keystone-chat-container.open { display: flex; }
@keyframes keystone-slide-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.keystone-chat-header {
  background: var(--keystone-primary);
  color: white;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.keystone-chat-header-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
}
.keystone-chat-header-avatar svg { width: 24px; height: 24px; fill: white; }
.keystone-chat-header-info { flex: 1; }
.keystone-chat-header-title { font-weight: 600; font-size: 16px; margin: 0; }
.keystone-chat-header-status { font-size: 12px; opacity: 0.9; }
.keystone-chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.keystone-message {
  max-width: 85%;
  padding: 12px 16px;
  border-radius: 18px;
  word-wrap: break-word;
}
.keystone-message-user {
  align-self: flex-end;
  background: var(--keystone-user-bg);
  color: var(--keystone-user-text);
  border-bottom-right-radius: 4px;
}
.keystone-message-bot {
  align-self: flex-start;
  background: var(--keystone-bot-bg);
  color: var(--keystone-bot-text);
  border-bottom-left-radius: 4px;
}
.keystone-typing {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 12px 16px;
  background: var(--keystone-bot-bg);
  border-radius: 18px;
  border-bottom-left-radius: 4px;
  align-self: flex-start;
}
.keystone-typing-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--keystone-text-light);
  animation: keystone-typing 1.4s ease-in-out infinite;
}
.keystone-typing-dot:nth-child(2) { animation-delay: 0.2s; }
.keystone-typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes keystone-typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-4px); opacity: 1; }
}
.keystone-chat-input-container {
  padding: 12px 16px;
  border-top: 1px solid var(--keystone-border);
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
.keystone-chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--keystone-border);
  border-radius: 24px;
  outline: none;
  font-size: 14px;
  font-family: inherit;
  resize: none;
  max-height: 100px;
  min-height: 44px;
}
.keystone-chat-input:focus {
  border-color: var(--keystone-primary);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}
.keystone-chat-send {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--keystone-primary);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.keystone-chat-send:hover { background: var(--keystone-primary-hover); }
.keystone-chat-send:disabled { background: var(--keystone-border); cursor: not-allowed; }
.keystone-chat-send svg { width: 20px; height: 20px; fill: white; }
.keystone-powered-by {
  text-align: center;
  padding: 8px;
  font-size: 11px;
  color: var(--keystone-text-light);
  border-top: 1px solid var(--keystone-border);
}
.keystone-powered-by a { color: var(--keystone-primary); text-decoration: none; }
@media (max-width: 480px) {
  .keystone-chat-widget { bottom: 10px; right: 10px; }
  .keystone-chat-container { width: calc(100vw - 20px); height: calc(100vh - 100px); bottom: 70px; right: -10px; }
  .keystone-chat-toggle { width: 54px; height: 54px; }
}`;
      document.head.appendChild(style);
    }
    
    createWidget() {
      const widget = document.createElement('div');
      widget.className = 'keystone-chat-widget';
      widget.id = 'keystone-chat-widget';
      
      widget.innerHTML = `
        <button class="keystone-chat-toggle" id="keystone-toggle">
          <svg class="keystone-icon-chat" viewBox="0 0 24 24">
            <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z"/>
          </svg>
          <svg class="keystone-icon-close" viewBox="0 0 24 24">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
          </svg>
        </button>
        
        <div class="keystone-chat-container" id="keystone-container">
          <div class="keystone-chat-header">
            <div class="keystone-chat-header-avatar">
              <svg viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
              </svg>
            </div>
            <div class="keystone-chat-header-info">
              <h3 class="keystone-chat-header-title">AI Assistant</h3>
              <span class="keystone-chat-header-status">Online</span>
            </div>
          </div>
          
          <div class="keystone-chat-messages" id="keystone-messages"></div>
          
          <div class="keystone-chat-input-container">
            <textarea 
              class="keystone-chat-input" 
              id="keystone-input" 
              placeholder="Type a message..."
              rows="1"
            ></textarea>
            <button class="keystone-chat-send" id="keystone-send">
              <svg viewBox="0 0 24 24">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
              </svg>
            </button>
          </div>
          
          <div class="keystone-powered-by">
            Powered by <a href="https://www.localkeystone.com" target="_blank">Keystone</a>
          </div>
        </div>
      `;
      
      document.body.appendChild(widget);
      
      this.elements = {
        widget,
        toggle: document.getElementById('keystone-toggle'),
        container: document.getElementById('keystone-container'),
        messages: document.getElementById('keystone-messages'),
        input: document.getElementById('keystone-input'),
        send: document.getElementById('keystone-send')
      };
    }
    
    bindEvents() {
      this.elements.toggle.addEventListener('click', () => this.toggleChat());
      this.elements.send.addEventListener('click', () => this.sendMessage());
      this.elements.input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
      
      this.elements.input.addEventListener('input', () => {
        this.elements.input.style.height = 'auto';
        this.elements.input.style.height = Math.min(this.elements.input.scrollHeight, 100) + 'px';
      });
    }
    
    toggleChat() {
      this.isOpen = !this.isOpen;
      this.elements.toggle.classList.toggle('open', this.isOpen);
      this.elements.container.classList.toggle('open', this.isOpen);
      
      if (this.isOpen && this.messages.length === 0) {
        this.fetchGreeting();
      }
      
      if (this.isOpen) {
        this.elements.input.focus();
        this.scrollToBottom();
      }
    }
    
    async loadHistory() {
      try {
        const response = await fetch(
          `${this.apiUrl}/chat/history/${this.businessId}/${this.sessionId}`
        );
        
        if (response.ok) {
          const data = await response.json();
          if (data.messages && data.messages.length > 0) {
            this.messages = data.messages;
            this.renderMessages();
          }
        }
      } catch (error) {
        console.error('Failed to load chat history:', error);
      }
    }
    
    async fetchGreeting() {
      try {
        const response = await fetch(
          `${this.apiUrl}/chat/greeting/${this.businessId}?session_id=${this.sessionId}`
        );
        
        if (response.ok) {
          const data = await response.json();
          
          const headerTitle = this.elements.container.querySelector('.keystone-chat-header-title');
          if (headerTitle && data.business_name) {
            headerTitle.textContent = data.business_name;
          }
          
          this.addMessage('bot', data.message);
        }
      } catch (error) {
        console.error('Failed to fetch greeting:', error);
        this.addMessage('bot', 'Hello! How can I help you today?');
      }
    }
    
    async sendMessage() {
      const message = this.elements.input.value.trim();
      if (!message || this.isLoading) return;
      
      this.elements.input.value = '';
      this.elements.input.style.height = 'auto';
      
      this.addMessage('user', message);
      this.showTyping();
      this.isLoading = true;
      this.elements.send.disabled = true;
      
      try {
        const response = await fetch(`${this.apiUrl}/chat/message`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            business_id: this.businessId,
            session_id: this.sessionId,
            message: message
          })
        });
        
        this.hideTyping();
        
        if (response.ok) {
          const data = await response.json();
          this.addMessage('bot', data.message);
        } else {
          this.addMessage('bot', 'Sorry, I encountered an error. Please try again.');
        }
      } catch (error) {
        console.error('Failed to send message:', error);
        this.hideTyping();
        this.addMessage('bot', 'Sorry, I couldn\'t connect to the server. Please try again later.');
      }
      
      this.isLoading = false;
      this.elements.send.disabled = false;
      this.elements.input.focus();
    }
    
    addMessage(role, content) {
      this.messages.push({ role, content, timestamp: new Date().toISOString() });
      this.renderMessage(role, content);
      this.scrollToBottom();
    }
    
    renderMessages() {
      this.elements.messages.innerHTML = '';
      for (const msg of this.messages) {
        this.renderMessage(msg.role === 'assistant' ? 'bot' : msg.role, msg.content);
      }
      this.scrollToBottom();
    }
    
    renderMessage(role, content) {
      const div = document.createElement('div');
      div.className = `keystone-message keystone-message-${role === 'user' ? 'user' : 'bot'}`;
      
      const formattedContent = this.formatMessage(content);
      div.innerHTML = formattedContent;
      
      this.elements.messages.appendChild(div);
    }
    
    formatMessage(content) {
      let formatted = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
      
      if (!formatted.startsWith('<p>')) {
        formatted = '<p>' + formatted + '</p>';
      }
      
      return formatted;
    }
    
    showTyping() {
      const typing = document.createElement('div');
      typing.className = 'keystone-typing';
      typing.id = 'keystone-typing';
      typing.innerHTML = `
        <span class="keystone-typing-dot"></span>
        <span class="keystone-typing-dot"></span>
        <span class="keystone-typing-dot"></span>
      `;
      this.elements.messages.appendChild(typing);
      this.scrollToBottom();
    }
    
    hideTyping() {
      const typing = document.getElementById('keystone-typing');
      if (typing) typing.remove();
    }
    
    scrollToBottom() {
      this.elements.messages.scrollTop = this.elements.messages.scrollHeight;
    }
  }
  
  function initWidget() {
    const script = document.currentScript || document.querySelector('script[data-business-id]');
    
    if (!script) {
      console.error('Keystone Chat: Could not find widget script tag');
      return;
    }
    
    const businessId = script.getAttribute('data-business-id');
    const apiUrl = script.getAttribute('data-api-url');
    
    if (!businessId) {
      console.error('Keystone Chat: data-business-id attribute is required');
      return;
    }
    
    window.keystoneChatWidget = new KeystoneChatWidget({
      businessId,
      apiUrl: apiUrl || DEFAULT_API_URL
    });
  }
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWidget);
  } else {
    initWidget();
  }
})();
