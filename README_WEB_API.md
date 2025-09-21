# 🌍 Travel Chatbot API

A powerful AI-powered travel assistant that can be easily integrated with any website. This chatbot provides personalized travel planning, budget optimization, and image recognition capabilities.

## ✨ Features

- **AI-Powered Travel Planning**: Intelligent trip recommendations based on user preferences
- **Image Recognition**: Upload photos of places for destination information (requires Google Vision API)
- **Session Management**: Maintains conversation context across multiple interactions
- **RESTful API**: Easy integration with any frontend (React, Vue, vanilla JS, etc.)
- **CORS Enabled**: Ready for cross-origin requests from web applications
- **Conversation Tracking**: Optional Langfuse integration for analytics
- **Multi-language Support**: Handles multiple languages for global users

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Clone or use the existing project
cd /path/to/Tripy_Ai_ChatBot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r reqironments.txt
pip install streamlit fastapi uvicorn langfuse google-cloud-vision flask flask-cors
```

### 2. Configure Environment Variables

```bash
# Copy the example configuration
cp config/.env.example config/.env

# Edit config/.env with your API keys
nano config/.env
```

**Required Configuration:**
```env
# OpenRouter/OpenAI API Key (Required)
API_KEY=your_openrouter_api_key_here

# Optional: Google Vision API for image processing
GOOGLE_APPLICATION_CREDENTIALS=path_to_your_google_service_account.json

# Optional: Langfuse for conversation tracking
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 3. Run the Server

```bash
# Using the deployment script (recommended)
./deploy.sh

# Or run directly
source venv/bin/activate
python web_app.py
```

The API will be available at: http://localhost:5001

## 📡 API Endpoints

### Health Check
```http
GET /health
```
Returns server status and feature availability.

### Chat with the Bot
```http
POST /chat
Content-Type: application/json

{
  "message": "Plan a 3-day trip to Paris for $1000",
  "session_id": "optional-session-id",
  "image": "optional-base64-encoded-image"
}
```

### Create New Session
```http
POST /sessions
```

### Get Bot Information
```http
GET /info
```

## 🔗 Website Integration

### TypeScript/JavaScript Example

```typescript
// Basic usage
const response = await fetch('http://localhost:5001/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    message: 'Plan a trip to Tokyo for 5 days' 
  })
});

const data = await response.json();
console.log(data.response); // AI response
```

### React Hook Example

```tsx
import { useTravelChatbot } from './typescript-integration';

function ChatComponent() {
  const { sendMessage, messages, isLoading } = useTravelChatbot();

  const handleSend = async () => {
    try {
      await sendMessage('Plan a weekend in New York');
    } catch (error) {
      console.error('Chat error:', error);
    }
  };

  return (
    <div>
      {messages.map((msg, i) => (
        <div key={i} className={msg.type}>
          {msg.content}
        </div>
      ))}
      <button onClick={handleSend} disabled={isLoading}>
        Send Message
      </button>
    </div>
  );
}
```

### Adding "Test Chatbot" Button to Your Website

```html
<!-- Add this button to your website -->
<button onclick="openChatbot()">Test Chatbot 🤖</button>

<script>
function openChatbot() {
  // Option 1: Open in new window
  window.open('http://localhost:5001/test', '_blank');
  
  // Option 2: Embed in iframe modal
  showChatModal();
}

function showChatModal() {
  const modal = document.createElement('div');
  modal.innerHTML = `
    <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0,0,0,0.8); z-index: 10000; display: flex; 
                align-items: center; justify-content: center;">
      <div style="width: 80%; height: 80%; background: white; border-radius: 10px; position: relative;">
        <button onclick="this.parentElement.parentElement.remove()" 
                style="position: absolute; top: 10px; right: 10px; background: #ff4444; 
                       color: white; border: none; border-radius: 50%; width: 30px; height: 30px;">×</button>
        <iframe src="http://localhost:5001/test" 
                style="width: 100%; height: 100%; border: none; border-radius: 10px;"></iframe>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}
</script>
```

## 🧪 Testing

1. **Test API Health**: Open http://localhost:5001/health
2. **Interactive Test Page**: Open http://localhost:5001/test (use test_api.html)
3. **Manual Testing**:

```bash
# Test health endpoint
curl http://localhost:5001/health

# Test chat endpoint
curl -X POST http://localhost:5001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a trip to Rome"}'
```

## 🔧 Configuration Options

### Port Configuration
```bash
# Change port (default: 5001)
export PORT=8080
python web_app.py
```

### CORS Configuration
Edit `config/.env`:
```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,https://yourdomain.com
```

### Database
The chatbot uses SQLite by default. The database file `travel_chats.db` will be created automatically.

## 🐛 Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r reqironments.txt
```

**2. API Key Issues**
- Make sure `API_KEY` is set in `config/.env`
- Use OpenRouter.ai or OpenAI API key
- Test the key independently

**3. Google Vision API Issues**
- Image processing will be disabled if credentials are missing
- This is optional - the bot works without it

**4. CORS Issues**
- Make sure your website domain is in `ALLOWED_ORIGINS`
- Check browser console for CORS errors

**5. Port Already in Use**
```bash
# Kill process using port 5001
lsof -ti:5001 | xargs kill -9

# Or use different port
export PORT=5002
python web_app.py
```

## 📁 Project Structure

```
Tripy_Ai_ChatBot/
├── web_app.py                    # Main Flask API server
├── main.py                       # Core chatbot logic
├── deploy.sh                     # Deployment script
├── test_api.html                 # Test interface
├── typescript-integration.ts     # TypeScript examples
├── config/
│   ├── .env                      # Environment variables
│   └── .env.example              # Configuration template
├── tools/                        # Chatbot tools (weather, etc.)
├── prompts/                      # AI prompts
├── db/                          # Database handling
└── streamlit_/                  # Original Streamlit components
```

## 🌟 Next Steps

1. **Get OpenRouter API Key**: Sign up at https://openrouter.ai/
2. **Configure Environment**: Add your API key to `config/.env`
3. **Test Integration**: Use the provided TypeScript examples
4. **Deploy**: Use the deployment script for production

## 🤝 Support

If you encounter any issues:
1. Check the troubleshooting section
2. Ensure all environment variables are set correctly
3. Verify the API is running with `curl http://localhost:5001/health`

## 🎯 Integration with Your TypeScript Website

Your website button should redirect to `http://localhost:5001/test` or use the provided TypeScript integration code to embed the chatbot directly in your site.

The chatbot is now ready to integrate with your website! 🚀