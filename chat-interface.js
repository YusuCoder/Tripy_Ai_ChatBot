/**
 * Tripy Chat Interface - JavaScript Implementation
 * Handles all chat functionality, API communication, and UI interactions
 */

class TripyChatInterface {
    constructor() {
        this.currentSessionId = null;
        this.sessions = [];
        this.messages = [];
        this.isTyping = false;
        this.isConnected = false;
        this.uploadedImage = null;
        this.apiBaseUrl = 'http://localhost:5001'; // Flask API URL
        
        this.initializeElements();
        this.setupEventListeners();
        this.initializeTheme();
        this.checkAPIConnection();
        this.loadSessions();
        this.createNewSession();
    }

    initializeElements() {
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.fileInput = document.getElementById('fileInput');
        this.fileUploadBtn = document.getElementById('fileUploadBtn');
        this.imagePreview = document.getElementById('imagePreview');
        this.previewImg = document.getElementById('previewImg');
        this.removeImageBtn = document.getElementById('removeImageBtn');
        this.sessionsContainer = document.getElementById('sessionsContainer');
        this.newChatBtn = document.getElementById('newChatBtn');
        this.sidebarToggle = document.getElementById('sidebarToggle');
        this.sidebar = document.getElementById('sidebar');
        this.themeToggle = document.getElementById('themeToggle');
        this.apiStatus = document.getElementById('apiStatus');
        this.visionStatus = document.getElementById('visionStatus');
        this.dbStatus = document.getElementById('dbStatus');
    }

    setupEventListeners() {
        // Send message
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Input handling
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
        });
        
        // File upload
        this.fileUploadBtn.addEventListener('click', () => {
            this.fileInput.click();
        });
        
        this.fileInput.addEventListener('change', (e) => {
            const file = e.target.files && e.target.files[0];
            if (file) {
                this.handleFileUpload(file);
            }
        });
        
        this.removeImageBtn.addEventListener('click', () => {
            this.removeUploadedImage();
        });
        
        // Session management
        this.newChatBtn.addEventListener('click', () => this.createNewSession());
        
        // UI controls
        this.sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        this.themeToggle.addEventListener('click', () => this.toggleTheme());
        
        // Responsive sidebar
        window.addEventListener('resize', () => {
            if (window.innerWidth > 768) {
                this.sidebar.classList.remove('open');
            }
        });
    }

    async checkAPIConnection() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            const data = await response.json();
            
            this.isConnected = data.status === 'healthy';
            this.updateStatusIndicators();
            
            if (this.isConnected) {
                console.log('✅ Connected to Tripy API');
            }
        } catch (error) {
            console.error('❌ Failed to connect to API:', error);
            this.isConnected = false;
            this.updateStatusIndicators();
        }
    }

    updateStatusIndicators() {
        // API Status
        this.apiStatus.className = `status-indicator ${this.isConnected ? 'success' : 'error'}`;
        
        // Vision Status (will be updated based on API response)
        this.visionStatus.className = 'status-indicator warning';
        
        // Database Status
        this.dbStatus.className = `status-indicator ${this.isConnected ? 'success' : 'error'}`;
    }

    async loadSessions() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/sessions`);
            const data = await response.json();
            
            if (data.success && data.data) {
                this.sessions = data.data.map((session) => ({
                    id: session.id,
                    name: session.name || `Chat ${this.sessions.length + 1}`,
                    created_at: new Date(session.created_at),
                    last_used: new Date(session.last_used),
                    message_count: session.message_count || 0
                }));
                
                this.renderSessions();
            }
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    }

    async createNewSession() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.session_id) {
                const newSession = {
                    id: data.session_id,
                    name: `Chat ${this.sessions.length + 1}`,
                    created_at: new Date(),
                    last_used: new Date(),
                    message_count: 0
                };
                
                this.sessions.unshift(newSession);
                this.switchToSession(newSession.id);
                this.renderSessions();
            }
        } catch (error) {
            console.error('Failed to create new session:', error);
        }
    }

    async switchToSession(sessionId) {
        this.currentSessionId = sessionId;
        this.messages = [];
        this.clearChat();
        
        // Update session list UI
        this.renderSessions();
        
        // Load session messages
        await this.loadSessionMessages(sessionId);
    }

    async loadSessionMessages(sessionId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/sessions/${sessionId}/messages`);
            const data = await response.json();
            
            if (data.success && data.data) {
                this.messages = data.data.map((msg) => ({
                    id: msg.id || this.generateId(),
                    origin: msg.origin,
                    message: msg.message,
                    timestamp: new Date(msg.timestamp),
                    image: msg.image
                }));
                
                this.renderMessages();
            }
        } catch (error) {
            console.error('Failed to load session messages:', error);
        }
    }

    async deleteSession(sessionId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/sessions/${sessionId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.status === 'deleted') {
                this.sessions = this.sessions.filter(s => s.id !== sessionId);
                
                if (this.currentSessionId === sessionId) {
                    if (this.sessions.length > 0) {
                        await this.switchToSession(this.sessions[0].id);
                    } else {
                        await this.createNewSession();
                    }
                }
                
                this.renderSessions();
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    }

    async sendMessage() {
        const text = this.messageInput.value.trim();
        
        if (!text && !this.uploadedImage) return;
        if (!this.currentSessionId) return;
        if (this.isTyping) return;

        // Create user message
        const userMessage = {
            id: this.generateId(),
            origin: 'human',
            message: text || 'Uploaded an image for analysis',
            timestamp: new Date(),
            image: this.uploadedImage ? await this.fileToBase64(this.uploadedImage) : undefined
        };

        // Add to messages and render
        this.messages.push(userMessage);
        this.renderMessage(userMessage);
        this.scrollToBottom();

        // Clear input
        this.messageInput.value = '';
        this.autoResizeTextarea();
        
        // Handle image
        const imageData = this.uploadedImage;
        this.removeUploadedImage();

        // Send to API
        await this.sendToAPI(text, imageData);
    }

    async sendToAPI(text, imageFile) {
        this.setTyping(true);
        
        try {
            const formData = new FormData();
            formData.append('message', text);
            formData.append('session_id', this.currentSessionId);
            
            if (imageFile) {
                formData.append('image', imageFile);
            }

            // Use streaming endpoint
            const response = await fetch(`${this.apiBaseUrl}/chat?stream=true`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`API request failed: ${response.status}`);
            }

            // Handle streaming response
            const reader = response.body && response.body.getReader();
            if (!reader) {
                throw new Error('No response stream available');
            }

            let assistantMessage = {
                id: this.generateId(),
                origin: 'assistant',
                message: '',
                timestamp: new Date()
            };

            this.messages.push(assistantMessage);
            const messageElement = this.renderMessage(assistantMessage);
            const messageText = messageElement.querySelector('.message-text');

            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6).trim();
                        if (data === '[DONE]') {
                            this.setTyping(false);
                            return;
                        }
                        
                        try {
                            const chunk = JSON.parse(data);
                            if (chunk.content) {
                                assistantMessage.message += chunk.content;
                                messageText.innerHTML = this.formatMessage(assistantMessage.message);
                                this.scrollToBottom();
                            } else if (chunk.error) {
                                throw new Error(chunk.error);
                            }
                        } catch (e) {
                            // Ignore parsing errors for partial chunks
                            console.warn('Failed to parse chunk:', data);
                        }
                    }
                }
            }

        } catch (error) {
            console.error('Failed to send message:', error);
            
            const errorMessage = {
                id: this.generateId(),
                origin: 'assistant',
                message: 'Sorry, I encountered an error. Please try again.',
                timestamp: new Date()
            };
            
            this.messages.push(errorMessage);
            this.renderMessage(errorMessage);
        }
        
        this.setTyping(false);
    }

    setTyping(typing) {
        this.isTyping = typing;
        this.sendBtn.disabled = typing;
        
        if (typing) {
            this.showTypingIndicator();
        } else {
            this.hideTypingIndicator();
        }
    }

    showTypingIndicator() {
        const existingIndicator = document.querySelector('.typing-indicator');
        if (existingIndicator) return;

        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant';
        typingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="message-content">
                <div class="typing-indicator">
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                    <span>Tripy is thinking...</span>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const indicator = document.querySelector('.typing-indicator');
        if (indicator) {
            const messageElement = indicator.closest('.message');
            if (messageElement) {
                messageElement.remove();
            }
        }
    }

    renderMessages() {
        this.clearChat();
        this.messages.forEach(message => this.renderMessage(message));
        this.scrollToBottom();
    }

    renderMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.origin}`;
        
        const avatar = message.origin === 'human' ? 
            '<i class="fas fa-user"></i>' : 
            '<i class="fas fa-robot"></i>';
        
        const imageHtml = message.image ? 
            `<img src="data:${message.image.type};base64,${message.image.data}" 
                  alt="${message.image.name}" 
                  class="message-image">` : '';
        
        messageDiv.innerHTML = `
            <div class="message-avatar">
                ${avatar}
            </div>
            <div class="message-content">
                <div class="message-bubble">
                    ${imageHtml}
                    <p class="message-text">${this.formatMessage(message.message)}</p>
                    <div class="message-timestamp">
                        ${this.formatTimestamp(message.timestamp)}
                    </div>
                </div>
            </div>
        `;
        
        this.chatMessages.appendChild(messageDiv);
        return messageDiv;
    }

    formatMessage(text) {
        // Convert URLs to links
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        text = text.replace(urlRegex, '<a href="$1" target="_blank" rel="noopener">$1</a>');
        
        // Convert line breaks to <br>
        text = text.replace(/\n/g, '<br>');
        
        return text;
    }

    formatTimestamp(date) {
        return date.toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }

    renderSessions() {
        this.sessionsContainer.innerHTML = '';
        
        this.sessions.forEach((session, index) => {
            const sessionDiv = document.createElement('div');
            sessionDiv.className = `session-item ${session.id === this.currentSessionId ? 'active' : ''}`;
            
            sessionDiv.innerHTML = `
                <div class="session-name">${session.name}</div>
                <button class="delete-btn" title="Delete session">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            
            // Session click handler
            sessionDiv.addEventListener('click', (e) => {
                if (!e.target.closest('.delete-btn')) {
                    this.switchToSession(session.id);
                }
            });
            
            // Delete button handler
            const deleteBtn = sessionDiv.querySelector('.delete-btn');
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (confirm('Are you sure you want to delete this chat session?')) {
                    this.deleteSession(session.id);
                }
            });
            
            this.sessionsContainer.appendChild(sessionDiv);
        });
    }

    async handleFileUpload(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please select an image file');
            return;
        }
        
        if (file.size > 10 * 1024 * 1024) { // 10MB limit
            alert('File size must be less than 10MB');
            return;
        }
        
        this.uploadedImage = file;
        
        // Show preview
        const reader = new FileReader();
        reader.onload = (e) => {
            this.previewImg.src = e.target.result;
            this.imagePreview.style.display = 'block';
        };
        reader.readAsDataURL(file);
    }

    removeUploadedImage() {
        this.uploadedImage = null;
        this.imagePreview.style.display = 'none';
        this.previewImg.src = '';
        this.fileInput.value = '';
    }

    async fileToBase64(file) {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = () => {
                const base64 = reader.result.split(',')[1];
                resolve({
                    data: base64,
                    name: file.name,
                    type: file.type
                });
            };
            reader.readAsDataURL(file);
        });
    }

    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    clearChat() {
        this.chatMessages.innerHTML = '';
    }

    scrollToBottom() {
        const chatContainer = document.getElementById('chatContainer');
        if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    }

    toggleSidebar() {
        this.sidebar.classList.toggle('open');
    }

    initializeTheme() {
        const savedTheme = localStorage.getItem('tripy-theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
        this.updateThemeIcon(savedTheme);
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('tripy-theme', newTheme);
        this.updateThemeIcon(newTheme);
    }

    updateThemeIcon(theme) {
        const icon = this.themeToggle.querySelector('i');
        icon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }

    generateId() {
        return Math.random().toString(36).substr(2, 9);
    }
}

// Initialize the chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new TripyChatInterface();
});