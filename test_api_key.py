#!/usr/bin/env python3
"""
Simple test to verify API key and OpenRouter connection
"""
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
print(f"API Key found: {bool(api_key)}")
print(f"API Key starts with: {api_key[:20] if api_key else 'None'}...")
print(f"API Key length: {len(api_key) if api_key else 0}")

if api_key:
    try:
        # Test OpenRouter connection
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=api_key,
            temperature=0.7,
            max_tokens=100,
        )
        
        # Simple test message
        response = llm.invoke("Hello, please respond with just 'Test successful'")
        print(f"✅ API Test successful: {response.content}")
        
    except Exception as e:
        print(f"❌ API Test failed: {e}")
else:
    print("❌ No API key found")