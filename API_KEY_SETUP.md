# API Key Setup Instructions

## The Issue
You're getting a 401 "No auth credentials found" or "User not found" error because the API key needs to be properly configured.

## Solutions

### Option 1: Use OpenRouter (Recommended)
1. Go to https://openrouter.ai/
2. Sign up and get your API key
3. Update your `.env` file with your OpenRouter API key:
   ```
   API_KEY=sk-or-v1-YOUR_ACTUAL_OPENROUTER_KEY_HERE
   ```

### Option 2: Use Direct OpenAI
1. Go to https://platform.openai.com/api-keys
2. Create an API key
3. Update your `.env` file:
   ```
   OPENAI_API_KEY=sk-YOUR_ACTUAL_OPENAI_KEY_HERE
   ```
4. Remove or comment out the API_KEY line

### Option 3: Test with a Valid Key
If you have a valid API key but it's not working:
1. Check if your OpenRouter account is active
2. Verify the key hasn't expired
3. Make sure you have credits/usage remaining

## Testing
After updating your `.env` file, restart the Streamlit app:
```bash
cd /home/rustam/projects/tripy-your-ai-travel-buddy/Tripy_Ai_ChatBot
/home/rustam/.local/bin/streamlit run streamlit_app.py --server.port 8503
```

## Current Status
- ✅ Environment loading: Working
- ✅ API key reading: Working  
- ❌ API authentication: **Needs valid key**
- ✅ All other components: Working

The chatbot is fully functional - it just needs a valid API key to connect to the AI service!