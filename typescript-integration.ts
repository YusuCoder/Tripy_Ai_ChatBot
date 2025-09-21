// TypeScript Integration Examples for Travel Chatbot API
// Use this code in your TypeScript website to integrate with the chatbot

// Types for the API
export interface ChatMessage {
  message: string;
  session_id?: string;
  image?: string; // Base64 encoded image
}

export interface ChatResponse {
  response: string;
  session_id: string;
  timestamp: string;
  status: string;
  features_used?: {
    image_processing: boolean;
    langfuse_tracking: boolean;
  };
}

export interface ChatbotInfo {
  name: string;
  description: string;
  features: string[];
  capabilities: {
    image_processing: boolean;
    langfuse_tracking: boolean;
    session_management: boolean;
  };
  version: string;
}

export interface HealthStatus {
  status: string;
  service: string;
  version: string;
  features: {
    langfuse_tracking: boolean;
    image_processing: boolean;
  };
  timestamp: string;
}

export class TravelChatbotAPI {
  private baseUrl: string;
  private sessionId: string | null = null;

  constructor(baseUrl: string = 'http://localhost:5001') {
    this.baseUrl = baseUrl;
  }

  // Health check
  async checkHealth(): Promise<HealthStatus> {
    const response = await fetch(`${this.baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.statusText}`);
    }
    return response.json();
  }

  // Get chatbot information
  async getChatbotInfo(): Promise<ChatbotInfo> {
    const response = await fetch(`${this.baseUrl}/info`);
    if (!response.ok) {
      throw new Error(`Failed to get chatbot info: ${response.statusText}`);
    }
    return response.json();
  }

  // Create a new session
  async createSession(): Promise<string> {
    const response = await fetch(`${this.baseUrl}/sessions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to create session: ${response.statusText}`);
    }

    const data = await response.json();
    this.sessionId = data.session_id;
    return data.session_id;
  }

  // Send a chat message
  async sendMessage(
    message: string, 
    imageFile?: File
  ): Promise<ChatResponse> {
    const payload: ChatMessage = {
      message,
    };

    // Add session ID if available
    if (this.sessionId) {
      payload.session_id = this.sessionId;
    }

    // Handle image upload
    if (imageFile) {
      payload.image = await this.fileToBase64(imageFile);
    }

    const response = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `Chat request failed: ${response.statusText}`);
    }

    const data: ChatResponse = await response.json();
    
    // Update session ID
    this.sessionId = data.session_id;
    
    return data;
  }

  // Convert file to base64
  private fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = error => reject(error);
    });
  }

  // Get current session ID
  getSessionId(): string | null {
    return this.sessionId;
  }

  // Set session ID manually
  setSessionId(sessionId: string): void {
    this.sessionId = sessionId;
  }

  // Clear session
  clearSession(): void {
    this.sessionId = null;
  }
}

// React Hook Example (if using React)
import { useState, useCallback } from 'react';

export function useTravelChatbot(apiUrl?: string) {
  const [api] = useState(() => new TravelChatbotAPI(apiUrl));
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [messages, setMessages] = useState<Array<{
    type: 'user' | 'bot';
    content: string;
    timestamp: Date;
    hasImage?: boolean;
  }>>([]);

  const sendMessage = useCallback(async (message: string, imageFile?: File) => {
    if (!message.trim() && !imageFile) return;

    setIsLoading(true);
    setError(null);

    // Add user message to chat
    const userMessage = {
      type: 'user' as const,
      content: message,
      timestamp: new Date(),
      hasImage: !!imageFile,
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await api.sendMessage(message, imageFile);
      
      // Add bot response to chat
      const botMessage = {
        type: 'bot' as const,
        content: response.response,
        timestamp: new Date(response.timestamp),
      };
      setMessages(prev => [...prev, botMessage]);
      
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      
      // Add error message to chat
      const errorBotMessage = {
        type: 'bot' as const,
        content: `Sorry, I encountered an error: ${errorMessage}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorBotMessage]);
      
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [api]);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    api.clearSession();
  }, [api]);

  const createNewSession = useCallback(async () => {
    try {
      await api.createSession();
      setMessages([]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session');
    }
  }, [api]);

  return {
    sendMessage,
    clearChat,
    createNewSession,
    messages,
    isLoading,
    error,
    sessionId: api.getSessionId(),
    api,
  };
}

// Vue.js Composable Example (if using Vue)
import { ref, reactive } from 'vue';

export function useTravelChatbotVue(apiUrl?: string) {
  const api = new TravelChatbotAPI(apiUrl);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const messages = reactive<Array<{
    type: 'user' | 'bot';
    content: string;
    timestamp: Date;
    hasImage?: boolean;
  }>>([]);

  const sendMessage = async (message: string, imageFile?: File) => {
    if (!message.trim() && !imageFile) return;

    isLoading.value = true;
    error.value = null;

    // Add user message
    messages.push({
      type: 'user',
      content: message,
      timestamp: new Date(),
      hasImage: !!imageFile,
    });

    try {
      const response = await api.sendMessage(message, imageFile);
      
      // Add bot response
      messages.push({
        type: 'bot',
        content: response.response,
        timestamp: new Date(response.timestamp),
      });
      
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      error.value = errorMessage;
      
      messages.push({
        type: 'bot',
        content: `Sorry, I encountered an error: ${errorMessage}`,
        timestamp: new Date(),
      });
      
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  const clearChat = () => {
    messages.splice(0);
    error.value = null;
    api.clearSession();
  };

  const createNewSession = async () => {
    try {
      await api.createSession();
      messages.splice(0);
      error.value = null;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to create session';
    }
  };

  return {
    sendMessage,
    clearChat,
    createNewSession,
    messages,
    isLoading,
    error,
    sessionId: api.getSessionId(),
    api,
  };
}

// Basic Usage Example
export async function basicUsageExample() {
  const chatbot = new TravelChatbotAPI('http://localhost:5001');

  try {
    // Check if API is healthy
    const health = await chatbot.checkHealth();
    console.log('Chatbot is healthy:', health);

    // Get chatbot info
    const info = await chatbot.getChatbotInfo();
    console.log('Chatbot info:', info);

    // Create a session
    await chatbot.createSession();

    // Send a message
    const response = await chatbot.sendMessage('Plan a 3-day trip to Paris for $1000');
    console.log('Bot response:', response.response);

    // Send message with image
    const fileInput = document.getElementById('imageInput') as HTMLInputElement;
    if (fileInput?.files?.[0]) {
      const imageResponse = await chatbot.sendMessage(
        'What can you tell me about this place?',
        fileInput.files[0]
      );
      console.log('Image analysis response:', imageResponse.response);
    }

  } catch (error) {
    console.error('Error:', error);
  }
}

// Integration with your website's "Test Chatbot" button
export function setupChatbotButton() {
  const testChatbotButton = document.getElementById('test-chatbot-btn');
  
  if (testChatbotButton) {
    testChatbotButton.addEventListener('click', () => {
      // Option 1: Open chatbot in new window
      window.open('http://localhost:5001/test', '_blank');
      
      // Option 2: Navigate to chatbot page
      // window.location.href = 'http://localhost:5001/test';
      
      // Option 3: Embed chatbot in modal (you'll need to implement the modal)
      // showChatbotModal();
    });
  }
}

// Error handling utility
export class ChatbotError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public originalError?: unknown
  ) {
    super(message);
    this.name = 'ChatbotError';
  }
}

export default TravelChatbotAPI;