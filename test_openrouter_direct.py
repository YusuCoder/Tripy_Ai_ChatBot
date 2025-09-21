#!/usr/bin/env python3

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the OpenRouter API key
api_key = os.getenv("API_KEY")

if api_key:
    print(f"OpenRouter API Key found: {api_key[:20]}...")
    print(f"Key length: {len(api_key)}")
    
    # Test with direct OpenRouter API
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "user", "content": "Say hello"}
            ],
            "max_tokens": 10
        }
        
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ OpenRouter API Test successful!")
            print(f"Response: {result['choices'][0]['message']['content']}")
        else:
            print(f"❌ OpenRouter API Test failed: {response.status_code} - {response.text}")
        
    except Exception as e:
        print(f"❌ OpenRouter API Test failed: {e}")
        
else:
    print("❌ No OpenRouter API key found")