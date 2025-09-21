#!/usr/bin/env python3

import os
from dotenv import load_dotenv
import openai

# Load environment variables
load_dotenv()

# Get the OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")

if api_key:
    print(f"OpenAI API Key found: {api_key[:20]}...")
    print(f"Key length: {len(api_key)}")
    
    # Test with direct OpenAI client
    try:
        client = openai.OpenAI(api_key=api_key)
        
        # Make a simple test request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say hello"}
            ],
            max_tokens=10
        )
        
        print("✅ OpenAI API Test successful!")
        print(f"Response: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ OpenAI API Test failed: {e}")
        
else:
    print("❌ No OpenAI API key found")