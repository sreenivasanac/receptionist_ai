/**
 * Keystone AI Receptionist Chat Widget
 * Embeddable chat widget for self-care businesses
 * With structured input support for services, datetime, and contact forms
 */

(function() {
  'use strict';

  const WIDGET_VERSION = '1.1.0';
  
  const DEFAULT_API_URL = 'http://localhost:8001';
  
  class KeystoneChatWidget {
    constructor(config) {
      this.businessId = config.businessId;
      this.apiUrl = config.apiUrl || DEFAULT_API_URL;
      this.sessionId = this.getOrCreateSessionId();
      this.isOpen = false;
      this.isLoading = false;
      this.messages = [];
      this.currentInputType = 'text';
      this.currentInputConfig = null;
      
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
  /* New Modern Palette matching Admin UI (Deep Slate & Indigo) */
  --keystone-primary: #6366f1; /* Indigo */
  --keystone-primary-hover: #4f46e5;
  --keystone-bg: #ffffff;
  --keystone-text: #1e293b; /* Slate 800 */
  --keystone-text-light: #64748b; /* Slate 500 */
  --keystone-border: #e2e8f0; /* Slate 200 */
  
  --keystone-user-bg: #6366f1;
  --keystone-user-text: #ffffff;
  
  --keystone-bot-bg: #f1f5f9; /* Slate 100 */
  --keystone-bot-text: #1e293b;
  
  /* Enhanced Shadows & Radius */
  --keystone-shadow: 
    0 4px 6px -1px rgba(0, 0, 0, 0.1),
    0 2px 4px -1px rgba(0, 0, 0, 0.06),
    0 20px 25px -5px rgba(0, 0, 0, 0.1);
  --keystone-radius: 20px;
  
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 15px;
  line-height: 1.6;
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 99999;
}

/* Import Inter font if not present in host */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

/* Chat Toggle Button */
.keystone-chat-toggle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--keystone-primary);
  border: none;
  cursor: pointer;
  box-shadow: 0 10px 15px -3px rgba(99, 102, 241, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.keystone-chat-toggle:hover {
  background: var(--keystone-primary-hover);
  transform: scale(1.05) translateY(-2px);
  box-shadow: 0 20px 25px -5px rgba(99, 102, 241, 0.4);
}

.keystone-chat-toggle:active {
  transform: scale(0.95);
}

.keystone-chat-toggle svg {
  width: 32px;
  height: 32px;
  fill: white;
  transition: transform 0.3s ease;
}

.keystone-chat-toggle.open .keystone-icon-chat {
  display: none;
}

.keystone-chat-toggle:not(.open) .keystone-icon-close {
  display: none;
}

.keystone-chat-toggle.open .keystone-icon-close {
  transform: rotate(90deg);
}

/* Chat Container */
.keystone-chat-container {
  position: absolute;
  bottom: 84px;
  right: 0;
  width: 400px; /* Slightly wider */
  max-width: calc(100vw - 48px);
  height: 650px; /* Taller */
  max-height: calc(100vh - 140px);
  background: var(--keystone-bg);
  border-radius: var(--keystone-radius);
  box-shadow: var(--keystone-shadow);
  display: none;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(226, 232, 240, 0.8);
  transform-origin: bottom right;
  animation: keystone-scale-in 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.keystone-chat-container.open {
  display: flex;
}

@keyframes keystone-scale-in {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

/* Chat Header */
.keystone-chat-header {
  background: var(--keystone-primary);
  background: linear-gradient(135deg, var(--keystone-primary), #4f46e5);
  color: white;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
  cursor: pointer;
  transition: background 0.2s ease;
  user-select: none;
}

.keystone-chat-header:hover {
  background: linear-gradient(135deg, #5558e8, #4338ca);
}

.keystone-chat-header:active {
  background: linear-gradient(135deg, #4f46e5, #3730a3);
}

.keystone-chat-header-avatar {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(4px);
}

.keystone-chat-header-avatar svg {
  width: 26px;
  height: 26px;
  fill: white;
}

.keystone-chat-header-info {
  flex: 1;
}

.keystone-chat-header-title {
  font-weight: 600;
  font-size: 17px;
  margin: 0;
  letter-spacing: -0.01em;
}

.keystone-chat-header-status {
  font-size: 13px;
  opacity: 0.9;
  display: flex;
  align-items: center;
  gap: 6px;
}

.keystone-chat-header-status::before {
  content: '';
  width: 6px;
  height: 6px;
  background-color: #4ade80;
  border-radius: 50%;
  display: block;
}

.keystone-chat-header-actions {
  display: flex;
  gap: 4px;
}

.keystone-chat-clear {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.15);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  position: relative;
}

.keystone-chat-clear::after {
  content: 'Reset conversation';
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  background: #1e293b;
  color: white;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.2s ease, visibility 0.2s ease;
  pointer-events: none;
  z-index: 100;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.keystone-chat-clear:hover::after {
  opacity: 1;
  visibility: visible;
}

.keystone-chat-clear:hover {
  background: rgba(255, 255, 255, 0.25);
}

.keystone-chat-clear svg {
  width: 18px;
  height: 18px;
  fill: white;
  transition: transform 0.2s ease;
}

.keystone-chat-clear:hover svg {
  transform: rotate(90deg);
}

.keystone-chat-minimize {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.7;
  transition: opacity 0.2s ease;
}

.keystone-chat-header:hover .keystone-chat-minimize {
  opacity: 1;
}

.keystone-chat-minimize svg {
  width: 20px;
  height: 20px;
  fill: white;
}

/* Chat Messages */
.keystone-chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background-color: #ffffff;
}

.keystone-message {
  max-width: 85%;
  padding: 14px 18px;
  border-radius: 20px;
  position: relative;
  font-size: 15px;
}

.keystone-message-user {
  align-self: flex-end;
  background: var(--keystone-user-bg);
  color: var(--keystone-user-text);
  border-bottom-right-radius: 4px;
  box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.2);
}

.keystone-message-bot {
  align-self: flex-start;
  background: var(--keystone-bot-bg);
  color: var(--keystone-bot-text);
  border-bottom-left-radius: 4px;
}

.keystone-message-bot strong {
  font-weight: 600;
  color: var(--keystone-primary);
}

/* Confirmation Overlay (In-chat) */
.keystone-confirm-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(4px);
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s ease;
}

.keystone-confirm-overlay.active {
  opacity: 1;
  pointer-events: auto;
}

.keystone-confirm-dialog {
  background: white;
  padding: 24px;
  border-radius: 16px;
  width: 80%;
  text-align: center;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
  border: 1px solid var(--keystone-border);
  transform: scale(0.95);
  transition: transform 0.2s ease;
}

.keystone-confirm-overlay.active .keystone-confirm-dialog {
  transform: scale(1);
}

.keystone-confirm-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--keystone-text);
}

.keystone-confirm-text {
  font-size: 14px;
  color: var(--keystone-text-light);
  margin-bottom: 20px;
}

.keystone-confirm-actions {
  display: flex;
  gap: 12px;
}

.keystone-btn {
  flex: 1;
  padding: 10px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.keystone-btn-primary {
  background: var(--keystone-primary);
  color: white;
}

.keystone-btn-primary:hover {
  background: var(--keystone-primary-hover);
}

.keystone-btn-secondary {
  background: var(--keystone-bot-bg);
  color: var(--keystone-text);
}

.keystone-btn-secondary:hover {
  background: #e2e8f0;
}

/* Typing Indicator */
.keystone-typing {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 16px 20px;
  background: var(--keystone-bot-bg);
  border-radius: 20px;
  border-bottom-left-radius: 4px;
  align-self: flex-start;
  width: fit-content;
}

.keystone-typing-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--keystone-text-light);
  animation: keystone-typing 1.4s ease-in-out infinite;
  opacity: 0.5;
}

/* Chat Input */
.keystone-chat-input-container {
  padding: 16px 20px;
  border-top: 1px solid var(--keystone-border);
  display: flex;
  gap: 12px;
  align-items: flex-end;
  background: white;
}

.keystone-chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid var(--keystone-border);
  border-radius: 12px;
  outline: none;
  font-size: 15px;
  font-family: inherit;
  resize: none;
  max-height: 120px;
  min-height: 46px;
  line-height: 1.5;
  background: #f8fafc;
  transition: all 0.2s;
}

.keystone-chat-input:focus {
  border-color: var(--keystone-primary);
  background: white;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.keystone-chat-send {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  background: var(--keystone-primary);
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.keystone-chat-send:hover {
  background: var(--keystone-primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.25);
}

.keystone-chat-send:active {
  transform: translateY(0);
}

.keystone-chat-send:disabled {
  background: var(--keystone-border);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.keystone-chat-send svg {
  width: 20px;
  height: 20px;
  fill: white;
}

/* Powered By */
.keystone-powered-by {
  text-align: center;
  padding: 10px;
  font-size: 11px;
  color: var(--keystone-text-light);
  background: #f8fafc;
  border-top: 1px solid var(--keystone-border);
}

/* Structured Input Updates */
.keystone-structured-input {
  padding: 16px 20px;
  border-top: 1px solid var(--keystone-border);
  background: #f8fafc;
  max-height: 350px;
  overflow-y: auto;
  box-sizing: border-box;
}

.keystone-service-item {
  border-radius: 12px;
  padding: 14px;
  background: white;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  border: 1px solid var(--keystone-border);
}

.keystone-service-item:hover {
  border-color: var(--keystone-primary);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
}

.keystone-submit-btn {
  padding: 14px;
  border-radius: 12px;
  font-weight: 600;
  letter-spacing: 0.01em;
  width: 100%;
  margin-top: 12px;
  background: var(--keystone-primary);
  color: white;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
}

.keystone-submit-btn:hover:not(:disabled) {
  background: var(--keystone-primary-hover);
}

.keystone-submit-btn:disabled {
  background: var(--keystone-border);
  cursor: not-allowed;
}

/* Service List */
.keystone-service-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 4px;
}

.keystone-service-item {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.keystone-service-item input {
  accent-color: var(--keystone-primary);
}

.keystone-service-item.selected {
  border-color: var(--keystone-primary);
  background: rgba(99, 102, 241, 0.05);
}

.keystone-service-info {
  flex: 1;
}

.keystone-service-name {
  font-weight: 500;
  color: var(--keystone-text);
}

.keystone-service-details {
  font-size: 13px;
  color: var(--keystone-text-light);
}

.keystone-service-price {
  font-weight: 600;
  color: var(--keystone-primary);
}

/* DateTime Picker */
.keystone-datetime-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.keystone-date-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--keystone-border);
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  background: white;
  color: var(--keystone-text);
  box-sizing: border-box;
}

.keystone-date-input:focus {
  outline: none;
  border-color: var(--keystone-primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.keystone-time-slots {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
  padding: 4px;
}

.keystone-time-slot {
  padding: 10px 8px;
  border: 1px solid var(--keystone-border);
  border-radius: 8px;
  background: white;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.keystone-time-slot:hover {
  border-color: var(--keystone-primary);
  background: rgba(99, 102, 241, 0.05);
}

.keystone-time-slot.selected {
  background: var(--keystone-primary);
  color: white;
  border-color: var(--keystone-primary);
}

.keystone-no-slots {
  color: var(--keystone-text-light);
  font-size: 14px;
  text-align: center;
  padding: 16px;
}

/* Contact Form */
.keystone-contact-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.keystone-form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.keystone-form-group label {
  font-size: 13px;
  font-weight: 500;
  color: var(--keystone-text);
}

.keystone-form-group input {
  padding: 12px 14px;
  border: 1px solid var(--keystone-border);
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  background: white;
  color: var(--keystone-text);
  width: 100%;
  box-sizing: border-box;
}

.keystone-form-group input::placeholder {
  color: var(--keystone-text-light);
}

.keystone-form-group input:focus {
  outline: none;
  border-color: var(--keystone-primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

/* Structured Input Header */
.keystone-structured-input h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--keystone-text);
}

/* Mobile Responsive */
@media (max-width: 480px) {
  .keystone-chat-widget {
    bottom: 16px;
    right: 16px;
  }
  
  .keystone-chat-container {
    width: calc(100vw - 32px);
    height: calc(100vh - 120px);
    bottom: 80px;
    right: 0;
  }
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
          <div class="keystone-chat-header" id="keystone-header" title="Click to minimize">
            <div class="keystone-chat-header-avatar">
              <svg viewBox="0 0 24 24">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
              </svg>
            </div>
            <div class="keystone-chat-header-info">
              <h3 class="keystone-chat-header-title">AI Assistant</h3>
              <span class="keystone-chat-header-status">Online</span>
            </div>
            <div class="keystone-chat-header-actions">
              <button class="keystone-chat-clear" id="keystone-clear">
                <svg viewBox="0 0 24 24">
                  <path d="M17.65 6.35A7.958 7.958 0 0012 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08A5.99 5.99 0 0112 18c-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
                </svg>
              </button>
              <div class="keystone-chat-minimize" title="Click to minimize">
                <svg viewBox="0 0 24 24">
                  <path d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/>
                </svg>
              </div>
            </div>
          </div>
          
          <div class="keystone-chat-messages" id="keystone-messages"></div>
          
          <div class="keystone-confirm-overlay" id="keystone-confirm-overlay">
            <div class="keystone-confirm-dialog">
              <h3 class="keystone-confirm-title">Reset Conversation?</h3>
              <p class="keystone-confirm-text">This will clear your current chat history and start fresh.</p>
              <div class="keystone-confirm-actions">
                <button class="keystone-btn keystone-btn-secondary" id="keystone-confirm-cancel">Cancel</button>
                <button class="keystone-btn keystone-btn-primary" id="keystone-confirm-yes">Yes, Reset</button>
              </div>
            </div>
          </div>
          
          <div id="keystone-structured-input"></div>
          
          <div class="keystone-chat-input-container" id="keystone-text-input">
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
        header: document.getElementById('keystone-header'),
        messages: document.getElementById('keystone-messages'),
        input: document.getElementById('keystone-input'),
        send: document.getElementById('keystone-send'),
        clear: document.getElementById('keystone-clear'),
        textInput: document.getElementById('keystone-text-input'),
        structuredInput: document.getElementById('keystone-structured-input'),
        confirmOverlay: document.getElementById('keystone-confirm-overlay'),
        confirmYes: document.getElementById('keystone-confirm-yes'),
        confirmCancel: document.getElementById('keystone-confirm-cancel')
      };
    }
    
    bindEvents() {
      this.elements.toggle.addEventListener('click', () => this.toggleChat());
      this.elements.send.addEventListener('click', () => this.sendMessage());
      this.elements.clear.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent header click from firing
        this.showResetConfirmation();
      });
      
      // Click on header to minimize chat
      this.elements.header.addEventListener('click', (e) => {
        // Don't minimize if clicking on action buttons
        if (e.target.closest('.keystone-chat-header-actions')) return;
        this.toggleChat();
      });
      
      this.elements.confirmCancel.addEventListener('click', () => {
        this.elements.confirmOverlay.classList.remove('active');
      });
      
      this.elements.confirmYes.addEventListener('click', () => {
        this.elements.confirmOverlay.classList.remove('active');
        this.clearSession();
      });
      
      this.elements.input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.sendMessage();
        }
      });
      
      this.elements.input.addEventListener('input', () => {
        this.elements.input.style.height = 'auto';
        this.elements.input.style.height = Math.min(this.elements.input.scrollHeight, 120) + 'px';
      });
    }
    
    showResetConfirmation() {
      if (this.isLoading) return;
      this.elements.confirmOverlay.classList.add('active');
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
    
    async sendMessage(messageOverride = null) {
      const message = messageOverride || this.elements.input.value.trim();
      if (!message || this.isLoading) return;
      
      if (!messageOverride) {
        this.elements.input.value = '';
        this.elements.input.style.height = 'auto';
      }
      
      // Hide structured input and show text input
      this.showTextInput();
      
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
          
          // Handle structured input based on response
          if (data.input_type && data.input_type !== 'text' && data.input_config) {
            this.showStructuredInput(data.input_type, data.input_config);
          }
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
    
    showTextInput() {
      this.elements.textInput.style.display = 'flex';
      this.elements.structuredInput.innerHTML = '';
      this.elements.structuredInput.style.display = 'none';
      this.currentInputType = 'text';
      this.currentInputConfig = null;
    }
    
    showStructuredInput(inputType, inputConfig) {
      this.currentInputType = inputType;
      this.currentInputConfig = inputConfig;
      
      this.elements.textInput.style.display = 'none';
      this.elements.structuredInput.style.display = 'block';
      
      let html = '<div class="keystone-structured-input">';
      
      switch (inputType) {
        case 'service_select':
          html += this.renderServiceSelect(inputConfig);
          break;
        case 'datetime_picker':
          html += this.renderDateTimePicker(inputConfig);
          break;
        case 'contact_form':
          html += this.renderContactForm(inputConfig);
          break;
        default:
          this.showTextInput();
          return;
      }
      
      html += '</div>';
      this.elements.structuredInput.innerHTML = html;
      this.bindStructuredInputEvents(inputType);
      this.scrollToBottom();
    }
    
    renderServiceSelect(config) {
      const services = config.services || [];
      const multiSelect = config.multi_select === true;  // Default to single-select
      
      let html = '<h4>Select a service:</h4>';
      html += '<div class="keystone-service-list">';
      
      services.forEach((service, index) => {
        const inputType = multiSelect ? 'checkbox' : 'radio';
        html += `
          <label class="keystone-service-item" data-service-id="${service.id}">
            <input type="${inputType}" name="service" value="${service.id}" data-name="${service.name}">
            <div class="keystone-service-info">
              <div class="keystone-service-name">${service.name}</div>
              <div class="keystone-service-details">
                ${service.duration_minutes ? service.duration_minutes + ' min' : ''}
                ${service.description ? ' • ' + service.description : ''}
              </div>
            </div>
            <div class="keystone-service-price">$${service.price}</div>
          </label>
        `;
      });
      
      html += '</div>';
      html += '<button class="keystone-submit-btn" id="keystone-submit-services">Continue</button>';
      
      return html;
    }
    
    renderDateTimePicker(config) {
      const minDate = config.min_date || new Date().toISOString().split('T')[0];
      const slots = config.slots || [];
      
      // Get unique dates that have slots
      const datesWithSlots = [...new Set(slots.map(s => s.date))].sort();
      const defaultDate = datesWithSlots[0] || minDate;
      
      // Get slots for the default date
      const slotsForDate = slots.filter(s => s.date === defaultDate);
      
      let html = '<h4>Select date and time:</h4>';
      html += '<div class="keystone-datetime-picker">';
      
      html += `<input type="date" class="keystone-date-input" id="keystone-date" min="${minDate}" value="${defaultDate}">`;
      
      html += '<div class="keystone-time-slots" id="keystone-time-slots-container">';
      if (slotsForDate.length > 0) {
        slotsForDate.forEach(slot => {
          const timeDisplay = this.formatTime(slot.time);
          const staffInfo = slot.staff_name ? ` (${slot.staff_name})` : '';
          html += `<button type="button" class="keystone-time-slot" data-slot-id="${slot.id}" data-time="${slot.time}" data-date="${slot.date}">${timeDisplay}${staffInfo}</button>`;
        });
      } else {
        html += '<p class="keystone-no-slots">No available times for this date</p>';
      }
      html += '</div>';
      
      html += '</div>';
      html += '<button class="keystone-submit-btn" id="keystone-submit-datetime" disabled>Continue</button>';
      
      return html;
    }
    
    formatTime(time24) {
      const [hours, minutes] = time24.split(':');
      const h = parseInt(hours, 10);
      const suffix = h >= 12 ? 'PM' : 'AM';
      const h12 = h % 12 || 12;
      return `${h12}:${minutes} ${suffix}`;
    }
    
    updateTimeSlotsForDate(date) {
      const config = this.currentInputConfig;
      if (!config || !config.slots) return;
      
      const slotsForDate = config.slots.filter(s => s.date === date);
      const container = this.elements.structuredInput.querySelector('#keystone-time-slots-container');
      const submitBtn = this.elements.structuredInput.querySelector('#keystone-submit-datetime');
      
      if (!container) return;
      
      let html = '';
      if (slotsForDate.length > 0) {
        slotsForDate.forEach(slot => {
          const timeDisplay = this.formatTime(slot.time);
          const staffInfo = slot.staff_name ? ` (${slot.staff_name})` : '';
          html += `<button type="button" class="keystone-time-slot" data-slot-id="${slot.id}" data-time="${slot.time}" data-date="${slot.date}">${timeDisplay}${staffInfo}</button>`;
        });
      } else {
        html = '<p class="keystone-no-slots">No available times for this date. Try a different date.</p>';
      }
      
      container.innerHTML = html;
      submitBtn.disabled = true;
      this.selectedSlotId = null;
      
      // Re-bind click events for new time slots
      const timeSlots = container.querySelectorAll('.keystone-time-slot');
      timeSlots.forEach(slot => {
        slot.addEventListener('click', () => {
          timeSlots.forEach(s => s.classList.remove('selected'));
          slot.classList.add('selected');
          this.selectedSlotId = slot.dataset.slotId;
          this.selectedSlotTime = slot.dataset.time;
          this.selectedSlotDate = slot.dataset.date;
          submitBtn.disabled = false;
        });
      });
    }
    
    renderContactForm(config) {
      const fields = config.fields || ['name', 'phone'];
      
      let html = '<h4>Your contact information:</h4>';
      html += '<div class="keystone-contact-form">';
      
      if (fields.includes('name') || fields.includes('first_name')) {
        html += `
          <div class="keystone-form-group">
            <label for="keystone-name">Name</label>
            <input type="text" id="keystone-name" placeholder="Your name" autocomplete="name">
          </div>
        `;
      }
      
      if (fields.includes('phone')) {
        html += `
          <div class="keystone-form-group">
            <label for="keystone-phone">Phone</label>
            <input type="tel" id="keystone-phone" placeholder="(555) 123-4567" autocomplete="tel">
          </div>
        `;
      }
      
      if (fields.includes('email')) {
        html += `
          <div class="keystone-form-group">
            <label for="keystone-email">Email</label>
            <input type="email" id="keystone-email" placeholder="you@example.com" autocomplete="email">
          </div>
        `;
      }
      
      html += '</div>';
      html += '<button class="keystone-submit-btn" id="keystone-submit-contact">Continue</button>';
      
      return html;
    }
    
    bindStructuredInputEvents(inputType) {
      switch (inputType) {
        case 'service_select':
          this.bindServiceSelectEvents();
          break;
        case 'datetime_picker':
          this.bindDateTimePickerEvents();
          break;
        case 'contact_form':
          this.bindContactFormEvents();
          break;
      }
    }
    
    bindServiceSelectEvents() {
      const items = this.elements.structuredInput.querySelectorAll('.keystone-service-item');
      const submitBtn = this.elements.structuredInput.querySelector('#keystone-submit-services');
      
      items.forEach(item => {
        item.addEventListener('click', (e) => {
          if (e.target.type !== 'checkbox' && e.target.type !== 'radio') {
            const input = item.querySelector('input');
            input.checked = !input.checked;
          }
          item.classList.toggle('selected', item.querySelector('input').checked);
        });
      });
      
      submitBtn.addEventListener('click', () => {
        const selected = [];
        this.elements.structuredInput.querySelectorAll('input:checked').forEach(input => {
          selected.push({
            id: input.value,
            name: input.dataset.name
          });
        });
        
        if (selected.length > 0) {
          // Send service ID in a parseable format for the backend
          const serviceIds = selected.map(s => s.id).join(', ');
          const serviceNames = selected.map(s => s.name).join(', ');
          const message = `I'd like to book: ${serviceNames} [service_id:${serviceIds}]`;
          this.sendMessage(message);
        }
      });
    }
    
    bindDateTimePickerEvents() {
      const timeSlots = this.elements.structuredInput.querySelectorAll('.keystone-time-slot');
      const submitBtn = this.elements.structuredInput.querySelector('#keystone-submit-datetime');
      const dateInput = this.elements.structuredInput.querySelector('#keystone-date');
      
      // Initialize selected slot tracking
      this.selectedSlotId = null;
      this.selectedSlotTime = null;
      this.selectedSlotDate = null;
      
      // Handle date change - update available time slots
      dateInput.addEventListener('change', (e) => {
        this.updateTimeSlotsForDate(e.target.value);
      });
      
      // Handle time slot selection
      timeSlots.forEach(slot => {
        slot.addEventListener('click', () => {
          timeSlots.forEach(s => s.classList.remove('selected'));
          slot.classList.add('selected');
          this.selectedSlotId = slot.dataset.slotId;
          this.selectedSlotTime = slot.dataset.time;
          this.selectedSlotDate = slot.dataset.date;
          submitBtn.disabled = false;
        });
      });
      
      // Handle submit
      submitBtn.addEventListener('click', () => {
        if (this.selectedSlotId && this.selectedSlotDate && this.selectedSlotTime) {
          const formattedDate = new Date(this.selectedSlotDate + 'T00:00:00').toLocaleDateString('en-US', {
            weekday: 'long',
            month: 'long',
            day: 'numeric'
          });
          const timeDisplay = this.formatTime(this.selectedSlotTime);
          // Include slot_id in a way the agent can parse it
          const message = `I'd like to book for ${formattedDate} at ${timeDisplay} [slot:${this.selectedSlotId}]`;
          this.sendMessage(message);
        }
      });
    }
    
    bindContactFormEvents() {
      const submitBtn = this.elements.structuredInput.querySelector('#keystone-submit-contact');
      
      submitBtn.addEventListener('click', () => {
        const nameInput = this.elements.structuredInput.querySelector('#keystone-name');
        const phoneInput = this.elements.structuredInput.querySelector('#keystone-phone');
        const emailInput = this.elements.structuredInput.querySelector('#keystone-email');
        
        const parts = [];
        if (nameInput && nameInput.value.trim()) {
          parts.push(`Name: ${nameInput.value.trim()}`);
        }
        if (phoneInput && phoneInput.value.trim()) {
          parts.push(`Phone: ${phoneInput.value.trim()}`);
        }
        if (emailInput && emailInput.value.trim()) {
          parts.push(`Email: ${emailInput.value.trim()}`);
        }
        
        if (parts.length > 0) {
          const message = parts.join(', ');
          this.sendMessage(message);
        }
      });
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
    
    async clearSession() {
      if (this.isLoading) return;
      
      this.elements.clear.disabled = true;
      
      try {
        await fetch(
          `${this.apiUrl}/chat/session/${this.businessId}/${this.sessionId}`,
          { method: 'DELETE' }
        );
      } catch (error) {
        console.error('Failed to clear session on server:', error);
      }
      
      const storageKey = `keystone_session_${this.businessId}`;
      localStorage.removeItem(storageKey);
      
      this.sessionId = 'sess_' + Math.random().toString(36).substr(2, 9) + Date.now().toString(36);
      localStorage.setItem(storageKey, this.sessionId);
      
      this.messages = [];
      this.elements.messages.innerHTML = '';
      this.showTextInput();
      
      await this.fetchGreeting();
      
      this.elements.clear.disabled = false;
      this.elements.input.focus();
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
