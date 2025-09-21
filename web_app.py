#!/usr/bin/env python3
"""
Web-compatible Flask API for the Travel Chatbot
This provides REST API endpoints that can be easily integrated with any frontend
"""

import os
import sys
import traceback
import base64
from io import BytesIO
from PIL import Image
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import json
from datetime import datetime

# Import your existing chatbot modules
from main import get_travel_agent, create_new_chat_session, get_session_history, LANGFUSE_ENABLED
from streamlit_.message_types import Message
from prompts.prompt import get_system_prompt
from langchain_core.messages import HumanMessage, SystemMessage

# Try to import Google Vision API
try:
    from google.cloud import vision
    # Test if credentials are available
    try:
        vision.ImageAnnotatorClient()
        VISION_ENABLED = True
        print("✅ Google Vision API loaded successfully with credentials")
    except Exception as cred_error:
        VISION_ENABLED = False
        print(f"⚠️ Google Vision API available but credentials missing: {cred_error}")
        print("   Image features will be disabled")
except ImportError:
    VISION_ENABLED = False
    print("⚠️ Google Vision API not available - image features disabled")

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Store active sessions in memory (you can enhance this with Redis later)
active_sessions = {}

class TravelChatbotAPI:
    def __init__(self):
        global VISION_ENABLED
        self.vision_client = None
        if VISION_ENABLED:
            try:
                self.vision_client = vision.ImageAnnotatorClient()
            except Exception as e:
                print(f"⚠️ Could not initialize Vision client: {e}")
                VISION_ENABLED = False
        
        print(f"🚀 Travel Chatbot API initialized")
        print(f"📊 Langfuse tracking: {'Enabled' if LANGFUSE_ENABLED else 'Disabled'}")
        print(f"👁️ Image processing: {'Enabled' if VISION_ENABLED else 'Disabled'}")
    
    def get_or_create_session(self, session_id=None):
        """Get existing session or create new one"""
        if not session_id:
            session_id = create_new_chat_session()
            print(f"🆕 Created new session: {session_id[:8]}...")
        
        if session_id not in active_sessions:
            try:
                agent, _ = get_travel_agent(session_id)
                active_sessions[session_id] = {
                    'agent': agent,
                    'created_at': datetime.now(),
                    'last_used': datetime.now()
                }
                print(f"💾 Loaded session: {session_id[:8]}...")
            except Exception as e:
                print(f"❌ Error creating session: {e}")
                raise
        else:
            active_sessions[session_id]['last_used'] = datetime.now()
        
        return session_id, active_sessions[session_id]['agent']
    
    def process_image_with_vision(self, image_data):
        """Process image with Google Vision API"""
        if not self.vision_client:
            return {
                'success': False,
                'error': 'Vision API not available',
                'landmarks': [],
                'labels': [],
                'text': ''
            }
        
        try:
            # Create vision API image object
            image = vision.Image(content=image_data)
            
            # Detect landmarks
            landmarks_response = self.vision_client.landmark_detection(image=image)
            landmarks = [
                {
                    'name': landmark.description,
                    'confidence': landmark.score
                }
                for landmark in landmarks_response.landmark_annotations[:3]
            ]
            
            # Detect labels
            labels_response = self.vision_client.label_detection(image=image)
            labels = [
                {
                    'name': label.description,
                    'confidence': label.score
                }
                for label in labels_response.label_annotations[:5]
            ]
            
            # Detect text
            text_response = self.vision_client.text_detection(image=image)
            text = text_response.text_annotations[0].description if text_response.text_annotations else ""
            
            return {
                'success': True,
                'landmarks': landmarks,
                'labels': labels,
                'text': text[:200] if text else ""  # Limit text length
            }
        
        except Exception as e:
            print(f"❌ Vision API error: {e}")
            return {
                'success': False,
                'error': str(e),
                'landmarks': [],
                'labels': [],
                'text': ''
            }
    
    def create_vision_prompt(self, vision_data, user_text=""):
        """Create comprehensive prompt combining user text and vision analysis"""
        prompt_parts = []
        
        if user_text.strip():
            prompt_parts.append(f"User question: {user_text}")
        
        if vision_data['success']:
            prompt_parts.append("I've uploaded an image. Here's what was detected:")
            
            if vision_data['landmarks']:
                landmarks_text = ", ".join([f"{l['name']} (confidence: {l['confidence']:.2f})" for l in vision_data['landmarks']])
                prompt_parts.append(f"Landmarks detected: {landmarks_text}")
            
            if vision_data['labels']:
                labels_text = ", ".join([f"{l['name']} ({l['confidence']:.2f})" for l in vision_data['labels']])
                prompt_parts.append(f"Scene elements: {labels_text}")
            
            if vision_data['text']:
                prompt_parts.append(f"Text in image: {vision_data['text']}")
            
            prompt_parts.append("Based on this image analysis and my question, please provide relevant travel advice, information about the location, or help with trip planning.")
        
        return " ".join(prompt_parts) if prompt_parts else "Hello! I'd like help with travel planning."

# Initialize the API
chatbot_api = TravelChatbotAPI()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Travel Chatbot API",
        "version": "1.0.0",
        "features": {
            "langfuse_tracking": LANGFUSE_ENABLED,
            "image_processing": VISION_ENABLED
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint with streaming support"""
    try:
        # Handle both JSON and FormData requests
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle file upload with FormData
            message = request.form.get('message', '').strip()
            session_id = request.form.get('session_id')
            uploaded_file = request.files.get('image')
            
            image_data = None
            if uploaded_file:
                image_data = uploaded_file.read()
        else:
            # Handle JSON request
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            message = data.get('message', '').strip()
            session_id = data.get('session_id')
            image_b64 = data.get('image')  # Base64 encoded image
            
            image_data = None
            if image_b64:
                try:
                    if ',' in image_b64:
                        image_b64 = image_b64.split(',')[1]  # Remove data:image/jpeg;base64, prefix
                    image_data = base64.b64decode(image_b64)
                except Exception as e:
                    return jsonify({"error": f"Invalid image data: {str(e)}"}), 400
        
        if not message and not image_data:
            return jsonify({"error": "Either message or image must be provided"}), 400
        
        # Get or create session
        session_id, agent = chatbot_api.get_or_create_session(session_id)
        
        # Process image if provided
        vision_data = None
        if image_data:
            try:
                vision_data = chatbot_api.process_image_with_vision(image_data)
                print(f"🖼️ Processed image with vision API")
            except Exception as e:
                print(f"❌ Image processing error: {e}")
                return jsonify({"error": f"Image processing failed: {str(e)}"}), 400
        
        # Create the prompt
        if vision_data:
            final_prompt = chatbot_api.create_vision_prompt(vision_data, message)
        else:
            final_prompt = message
        
        print(f"💬 Processing: {final_prompt[:100]}...")
        
        # Check if streaming is requested
        stream = request.args.get('stream', 'false').lower() == 'true'
        
        if stream:
            return stream_chat_response(agent, final_prompt, session_id)
        else:
            return generate_chat_response(agent, final_prompt, session_id)
            
    except Exception as e:
        print(f"❌ Chat endpoint error: {e}")
        traceback.print_exc()
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }), 500

def stream_chat_response(agent, prompt, session_id):
    """Generate streaming chat response"""
    def generate():
        try:
            messages = [SystemMessage(content=get_system_prompt())]
            
            # Add chat history if available
            try:
                session_history = get_session_history(session_id)
                if hasattr(session_history, 'messages'):
                    messages.extend(session_history.messages)
            except Exception as history_error:
                print(f"⚠️ Could not load chat history: {history_error}")
            
            # Add current user input
            messages.append(HumanMessage(content=prompt))
            
            # Stream response from agent
            for chunk in agent.stream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"
            
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            print(f"❌ Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    from flask import Response
    return Response(
        generate(), 
        mimetype='text/plain',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

def generate_chat_response(agent, prompt, session_id):
    """Generate regular (non-streaming) chat response"""
    try:
        messages = [SystemMessage(content=get_system_prompt())]
        
        # Add chat history if available
        try:
            session_history = get_session_history(session_id)
            if hasattr(session_history, 'messages'):
                messages.extend(session_history.messages)
        except Exception as history_error:
            print(f"⚠️ Could not load chat history: {history_error}")
        
        # Add current user input
        messages.append(HumanMessage(content=prompt))
        
        # Check if this is a travel planning request
        travel_keywords = ['trip', 'travel', 'plan', 'visit', 'itinerary', 'vacation', 'holiday', 'journey']
        preference_keywords = ['prefer', 'love', 'like', 'enjoy', 'interested', 'want to see', 'museums', 'nightlife', 'food', 'historical', 'religious', 'parks', 'clubs', 'cuisine', 'tours', 'affordable']
        
        is_travel_request = (any(keyword in prompt.lower() for keyword in travel_keywords) or 
                           any(keyword in prompt.lower() for keyword in preference_keywords))
        
        if is_travel_request:
            print(f"🌍 Detected travel planning request - using direct tool approach")
            return handle_travel_planning_directly(prompt, session_id)
        
        # Regular response for non-travel requests
        response = agent.agent_executor.invoke({
            "input": prompt,
            "chat_history": []
        })
        
        # Extract travel plan from agent response if available
        ai_response = None
        
        # Try to extract the complete travel plan from tool outputs
        if isinstance(response, dict) and 'intermediate_steps' in response:
            print(f"🔍 Found {len(response['intermediate_steps'])} intermediate steps")
            
            # Check if we have travel planning tool output
            has_travel_plan = False
            for step in response['intermediate_steps']:
                if len(step) >= 2:
                    action, observation = step
                    if hasattr(action, 'tool') and action.tool == 'create_travel_plan':
                        # Found the travel plan tool output - use it directly
                        ai_response = observation
                        has_travel_plan = True
                        print(f"✅ Extracted full travel plan from tool output: {len(ai_response)} characters")
                        break
                    elif hasattr(action, 'log') and 'create_travel_plan' in action.log:
                        # Alternative way to detect travel planning tool
                        ai_response = observation
                        has_travel_plan = True
                        print(f"✅ Extracted travel plan via log detection: {len(ai_response)} characters")
                        break
            
            # If travel request but no travel plan found, return error message
            if is_travel_request and not has_travel_plan:
                print(f"⚠️ Travel request detected but no travel plan generated")
                ai_response = "I apologize, but I was unable to generate a complete travel plan. Please try rephrasing your request or contact support if the issue persists."
        
        # If no travel plan found in intermediate steps, use the final response
        if not ai_response:
            if isinstance(response, dict) and 'output' in response:
                ai_response = response['output']
            elif isinstance(response, dict) and 'content' in response:
                ai_response = response['content']
            elif hasattr(response, 'content'):
                ai_response = response.content
            elif isinstance(response, str):
                ai_response = response
            else:
                ai_response = str(response)
            print(f"✅ Using final response: {len(ai_response)} characters")
        
        return jsonify({
            "response": ai_response,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "features_used": {
                "image_processing": bool(prompt != messages[-1].content),
                "langfuse_tracking": LANGFUSE_ENABLED,
                "travel_planning_enforced": is_travel_request
            }
        })
        
    except Exception as e:
        print(f"❌ Agent error: {e}")
        traceback.print_exc()
        return jsonify({
            "error": f"Failed to generate response: {str(e)}",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }), 500

def handle_travel_planning_directly(prompt, session_id):
    """Handle travel planning by calling tools directly with preference collection"""
    try:
        print(f"🔄 Starting intelligent travel planning workflow...")
        
        # Check if preferences are already provided in the prompt
        has_preferences = any(word in prompt.lower() for word in [
            "museum", "night", "food", "budget", "nature", "adventure", 
            "relaxation", "shopping", "architecture", "photography", "prefer",
            "love", "like", "enjoy", "interested", "historical", "religious",
            "parks", "clubs", "cuisine", "tours", "affordable", "cultural"
        ])
        
        # Check if this looks like a destination + preferences format
        has_destination_context = any(word in prompt.lower() for word in [
            "tokyo", "paris", "london", "japan", "france", "uk", "italy", 
            "spain", "germany", "thailand", "day", "days", "week"
        ])
        
        if not has_preferences and not has_destination_context:
            # Ask for preferences first
            preference_prompt = f"""
🎯 **To create your perfect travel plan, please tell me:**

1. **Where would you like to go?** (e.g., Tokyo, Paris, London, etc.)
2. **How many days?** (e.g., 3 days, 1 week)
3. **What interests you most?**

**Interest options:**
- 🏛️ **Museums & Culture** - Art galleries, historical sites, cultural experiences
- 🌃 **Nightlife & Entertainment** - Bars, clubs, live music, evening activities  
- 🍽️ **Food & Dining** - Local cuisine, fine dining, street food, cooking experiences
- 🏞️ **Nature & Outdoors** - Parks, gardens, hiking, scenic views
- 🛍️ **Shopping** - Markets, boutiques, local crafts, souvenirs
- 🏛️ **Architecture & History** - Historical buildings, religious sites, landmarks
- 🎢 **Adventure & Activities** - Sports, tours, unique experiences
- 😌 **Relaxation** - Spas, peaceful spots, leisurely activities
- 📸 **Photography** - Instagram-worthy spots, scenic viewpoints
- 💰 **Budget-Friendly** - Free activities, affordable options

**Example:** "Plan a 5-day trip to Tokyo, I love museums, historical sites, and local cuisine"
"""
            
            return jsonify({
                "response": preference_prompt,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "status": "preference_collection",
                "workflow": "collecting_preferences",
                "next_step": "waiting_for_preferences"
            })
        
        # Step 1: Extract destination from prompt or use a default
        destination = extract_destination_from_prompt(prompt)
        
        # If no destination found and this looks like just preferences, ask for destination
        if destination in ["Paris,FR", "Visit"] and not any(city in prompt.lower() for city in ["paris", "tokyo", "london", "japan", "france", "uk"]):
            return jsonify({
                "response": f"""
🗺️ **I see you have great preferences: {prompt}**

But I need to know **where you'd like to travel**! Please tell me:

**Which destination interests you?**
- 🗾 **Tokyo, Japan** - Amazing temples, museums, incredible food culture
- 🗼 **Paris, France** - World-class museums, historic architecture, fine dining  
- 🏰 **London, UK** - Rich history, great museums, traditional pubs
- 🍝 **Rome, Italy** - Ancient history, religious sites, amazing cuisine
- 🏛️ **Other destination** - Just name any city you'd like to visit!

**Example:** "I want to visit Tokyo for 5 days" or "Plan a trip to Paris"

Once you tell me the destination and duration, I'll create a perfect travel plan based on your interests in historical sites, local cuisine, parks, religious sites, tours, and affordable options! 🎯
""",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "status": "destination_needed",
                "workflow": "awaiting_destination"
            })
        
        print(f"📍 Detected destination: {destination}")
        
        # Step 2: Get weather directly
        try:
            from tools.weather_tool import WeatherTool
            weather_tool = WeatherTool()
            weather_result = weather_tool._run(destination)
            print(f"🌤️ Weather obtained: {weather_result[:100]}...")
        except Exception as weather_error:
            print(f"⚠️ Weather error: {weather_error}")
            weather_result = "Weather information unavailable"
        
        # Step 3: Generate travel plan directly with preferences
        try:
            from tools.travel_planning_tool_new import TravelPlanningTool
            travel_tool = TravelPlanningTool()
            
            # Create enhanced query with weather info and preferences
            enhanced_query = f"{prompt}, weather: {weather_result}"
            travel_plan = travel_tool._run(enhanced_query)
            print(f"✅ Generated personalized travel plan: {len(travel_plan)} characters")
            
            return jsonify({
                "response": travel_plan,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "workflow": "personalized_travel_planning",
                "features_used": {
                    "weather_check": True,
                    "travel_planning": True,
                    "preference_based": True,
                    "location_specific": True,
                    "direct_tool_execution": True,
                    "langfuse_tracking": LANGFUSE_ENABLED
                }
            })
        except Exception as travel_error:
            print(f"❌ Travel planning error: {travel_error}")
            return jsonify({
                "error": f"Travel planning failed: {str(travel_error)}",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }), 500
        
    except Exception as e:
        print(f"❌ Direct travel planning workflow error: {e}")
        traceback.print_exc()
        return jsonify({
            "error": f"Failed to generate travel plan: {str(e)}",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }), 500

def extract_destination_from_prompt(prompt):
    """Extract destination from user prompt"""
    prompt_lower = prompt.lower()
    
    # Common destination patterns
    destinations = {
        'japan': 'Tokyo,JP',
        'tokyo': 'Tokyo,JP',
        'paris': 'Paris,FR',
        'france': 'Paris,FR',
        'london': 'London,UK',
        'uk': 'London,UK',
        'england': 'London,UK',
        'italy': 'Rome,IT',
        'rome': 'Rome,IT',
        'germany': 'Berlin,DE',
        'berlin': 'Berlin,DE',
        'spain': 'Madrid,ES',
        'madrid': 'Madrid,ES',
        'barcelona': 'Barcelona,ES',
        'new york': 'New York,US',
        'nyc': 'New York,US',
        'usa': 'New York,US',
        'america': 'New York,US',
        'thailand': 'Bangkok,TH',
        'bangkok': 'Bangkok,TH',
        'india': 'Delhi,IN',
        'delhi': 'Delhi,IN',
        'mumbai': 'Mumbai,IN',
        'australia': 'Sydney,AU',
        'sydney': 'Sydney,AU',
        'canada': 'Toronto,CA',
        'toronto': 'Toronto,CA',
        'iceland': 'Reykjavik,IS',
        'reykjavik': 'Reykjavik,IS',
        'norway': 'Oslo,NO',
        'oslo': 'Oslo,NO',
        'sweden': 'Stockholm,SE',
        'stockholm': 'Stockholm,SE'
    }
    
    # Look for destination in prompt
    for dest_key, dest_value in destinations.items():
        if dest_key in prompt_lower:
            return dest_value
    
    # If no specific destination found, try to extract from "to" patterns
    words = prompt.split()
    for i, word in enumerate(words):
        if word.lower() in ['to', 'in', 'visit', 'visiting']:
            if i + 1 < len(words):
                next_word = words[i + 1].strip('.,!?')
                if next_word.lower() in destinations:
                    return destinations[next_word.lower()]
                else:
                    return next_word.title()  # Return capitalized city name
    
    # Default fallback
    return "Paris,FR"

@app.route('/sessions', methods=['POST'])
def create_session():
    """Create a new chat session"""
    try:
        session_id = create_new_chat_session()
        return jsonify({
            "session_id": session_id,
            "status": "created",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a chat session"""
    try:
        # Remove from active sessions
        if session_id in active_sessions:
            del active_sessions[session_id]
        
        return jsonify({
            "status": "deleted",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sessions', methods=['GET'])
def get_sessions():
    """Get all chat sessions"""
    try:
        from main import get_all_chat_sessions
        sessions = get_all_chat_sessions()
        
        sessions_data = []
        for session_id in sessions:
            session_info = {
                "id": session_id,
                "name": f"Chat Session",
                "created_at": datetime.now().isoformat(),  # You can enhance this with actual data
                "last_used": datetime.now().isoformat(),
                "message_count": 0  # You can enhance this with actual message count
            }
            sessions_data.append(session_info)
        
        return jsonify({
            "success": True,
            "data": sessions_data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/sessions/<session_id>/messages', methods=['GET'])
def get_session_messages(session_id):
    """Get messages for a specific session"""
    try:
        from main import get_chat_history_for_session
        
        # Get chat history from database
        history = get_chat_history_for_session(session_id)
        messages = []
        
        if hasattr(history, 'messages'):
            for msg in history.messages:
                message_data = {
                    "id": str(len(messages) + 1),
                    "origin": "human" if hasattr(msg, 'type') and msg.type == 'human' else "assistant",
                    "message": msg.content if hasattr(msg, 'content') else str(msg),
                    "timestamp": datetime.now().isoformat()
                }
                messages.append(message_data)
        
        return jsonify({
            "success": True,
            "data": messages,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error getting session messages: {e}")
        return jsonify({
            "success": True,
            "data": [],  # Return empty array instead of error for better UX
            "session_id": session_id,
            "error": str(e)
        })

@app.route('/info', methods=['GET'])
def get_info():
    """Get chatbot information"""
    return jsonify({
        "name": "Tripy - AI Travel Assistant",
        "description": "Your intelligent travel planning companion powered by advanced AI",
        "features": [
            "Personalized trip planning",
            "Budget optimization",
            "Image recognition for landmarks and places",
            "Real-time travel advice",
            "Multi-language support",
            "Conversation memory"
        ],
        "capabilities": {
            "image_processing": VISION_ENABLED,
            "langfuse_tracking": LANGFUSE_ENABLED,
            "session_management": True
        },
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/test', methods=['GET'])
def test_interface():
    """Serve the test interface"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Travel Chatbot API Test</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        h1 {
            color: #4a5568;
            text-align: center;
            margin-bottom: 30px;
        }
        .chat-container {
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            height: 400px;
            overflow-y: auto;
            padding: 15px;
            margin-bottom: 20px;
            background: #f8fafc;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 8px;
        }
        .user-message {
            background: #4299e1;
            color: white;
            margin-left: 20%;
        }
        .bot-message {
            background: #48bb78;
            color: white;
            margin-right: 20%;
        }
        .input-container {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        input[type="text"] {
            flex: 1;
            padding: 12px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 16px;
        }
        input[type="file"] {
            padding: 8px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
        }
        button {
            padding: 12px 20px;
            background: #4299e1;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        button:hover {
            background: #3182ce;
        }
        button:disabled {
            background: #a0aec0;
            cursor: not-allowed;
        }
        .status {
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
            font-weight: bold;
        }
        .status.success {
            background: #c6f6d5;
            color: #2f855a;
        }
        .status.error {
            background: #fed7d7;
            color: #c53030;
        }
        .status.loading {
            background: #bee3f8;
            color: #2b6cb0;
        }
        .endpoints {
            background: #f0f4f8;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .endpoints h3 {
            margin-top: 0;
            color: #2d3748;
        }
        .endpoint {
            font-family: monospace;
            background: white;
            padding: 8px;
            border-radius: 4px;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌍 Travel Chatbot API Test</h1>
        
        <div id="status" class="status" style="display: none;"></div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message bot-message">
                <strong>Tripy:</strong> Hello! I'm your AI travel assistant. Ask me anything about travel planning!
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="messageInput" placeholder="Ask me about travel plans, destinations, or upload an image..." />
            <input type="file" id="imageInput" accept="image/*" />
            <button onclick="sendMessage()" id="sendButton">Send</button>
        </div>
        
        <div class="input-container">
            <button onclick="testHealth()" style="background: #48bb78;">Test Health</button>
            <button onclick="getInfo()" style="background: #ed8936;">Get Info</button>
            <button onclick="createSession()" style="background: #9f7aea;">New Session</button>
            <button onclick="clearChat()" style="background: #e53e3e;">Clear Chat</button>
        </div>

        <div class="endpoints">
            <h3>📡 Available API Endpoints:</h3>
            <div class="endpoint">GET /health - Health check</div>
            <div class="endpoint">POST /chat - Send message to chatbot</div>
            <div class="endpoint">GET /info - Get chatbot information</div>
            <div class="endpoint">POST /sessions - Create new session</div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin;
        let currentSessionId = null;

        function showStatus(message, type = 'loading') {
            const statusDiv = document.getElementById('status');
            statusDiv.textContent = message;
            statusDiv.className = `status ${type}`;
            statusDiv.style.display = 'block';
            
            if (type !== 'loading') {
                setTimeout(() => {
                    statusDiv.style.display = 'none';
                }, 3000);
            }
        }

        function addMessage(sender, message, isError = false) {
            const chatContainer = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender === 'You' ? 'user-message' : 'bot-message'}`;
            if (isError) messageDiv.style.background = '#e53e3e';
            
            messageDiv.innerHTML = `<strong>${sender}:</strong> ${message}`;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        async function sendMessage() {
            const messageInput = document.getElementById('messageInput');
            const imageInput = document.getElementById('imageInput');
            const sendButton = document.getElementById('sendButton');
            
            const message = messageInput.value.trim();
            const imageFile = imageInput.files[0];
            
            if (!message && !imageFile) {
                showStatus('Please enter a message or select an image', 'error');
                return;
            }

            // Disable input while processing
            sendButton.disabled = true;
            showStatus('Sending message...', 'loading');

            // Add user message to chat
            if (message) {
                addMessage('You', message);
            }
            if (imageFile) {
                addMessage('You', `📷 Uploaded image: ${imageFile.name}`);
            }

            try {
                const payload = { message };
                
                if (currentSessionId) {
                    payload.session_id = currentSessionId;
                }

                // Handle image upload
                if (imageFile) {
                    const reader = new FileReader();
                    reader.onload = async function(e) {
                        payload.image = e.target.result;
                        await sendChatRequest(payload);
                    };
                    reader.readAsDataURL(imageFile);
                } else {
                    await sendChatRequest(payload);
                }

            } catch (error) {
                addMessage('Error', error.message, true);
                showStatus('Failed to send message', 'error');
            } finally {
                sendButton.disabled = false;
                messageInput.value = '';
                imageInput.value = '';
            }
        }

        async function sendChatRequest(payload) {
            const response = await fetch(`${API_BASE}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                addMessage('Tripy', data.response);
                currentSessionId = data.session_id;
                showStatus('Message sent successfully!', 'success');
            } else {
                addMessage('Error', data.error || 'Unknown error occurred', true);
                showStatus(`Error: ${data.error}`, 'error');
            }
        }

        async function testHealth() {
            showStatus('Testing health endpoint...', 'loading');
            try {
                const response = await fetch(`${API_BASE}/health`);
                const data = await response.json();
                
                if (response.ok) {
                    addMessage('System', `Health check passed! Status: ${data.status}, Features: ${JSON.stringify(data.features)}`);
                    showStatus('Health check successful!', 'success');
                } else {
                    addMessage('System', 'Health check failed', true);
                    showStatus('Health check failed', 'error');
                }
            } catch (error) {
                addMessage('System', `Connection error: ${error.message}`, true);
                showStatus('Cannot connect to API server', 'error');
            }
        }

        async function getInfo() {
            showStatus('Getting chatbot info...', 'loading');
            try {
                const response = await fetch(`${API_BASE}/info`);
                const data = await response.json();
                
                if (response.ok) {
                    addMessage('System', `${data.name}: ${data.description}. Features: ${data.features.join(', ')}`);
                    showStatus('Info retrieved successfully!', 'success');
                } else {
                    addMessage('System', 'Failed to get info', true);
                    showStatus('Failed to get info', 'error');
                }
            } catch (error) {
                addMessage('System', `Connection error: ${error.message}`, true);
                showStatus('Cannot connect to API server', 'error');
            }
        }

        async function createSession() {
            showStatus('Creating new session...', 'loading');
            try {
                const response = await fetch(`${API_BASE}/sessions`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                const data = await response.json();
                
                if (response.ok) {
                    currentSessionId = data.session_id;
                    addMessage('System', `New session created: ${data.session_id.substring(0, 8)}...`);
                    showStatus('New session created!', 'success');
                } else {
                    addMessage('System', 'Failed to create session', true);
                    showStatus('Failed to create session', 'error');
                }
            } catch (error) {
                addMessage('System', `Connection error: ${error.message}`, true);
                showStatus('Cannot connect to API server', 'error');
            }
        }

        function clearChat() {
            const chatContainer = document.getElementById('chatContainer');
            chatContainer.innerHTML = '<div class="message bot-message"><strong>Tripy:</strong> Hello! I\\'m your AI travel assistant. Ask me anything about travel planning!</div>';
            showStatus('Chat cleared!', 'success');
        }

        // Allow Enter key to send message
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Test connection on page load
        window.onload = function() {
            testHealth();
        };
    </script>
</body>
</html>'''

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Endpoint not found",
        "available_endpoints": [
            "GET /health - Health check",
            "POST /chat - Main chat endpoint",
            "POST /sessions - Create new session",
            "DELETE /sessions/<id> - Delete session",
            "GET /info - Get chatbot info"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error",
        "message": "Something went wrong on our end"
    }), 500

if __name__ == '__main__':
    print("🌍 Starting Travel Chatbot API Server...")
    print("📍 Available endpoints:")
    print("   GET  /health          - Health check")
    print("   POST /chat            - Main chat endpoint")
    print("   POST /sessions        - Create new session")
    print("   DELETE /sessions/<id> - Delete session")
    print("   GET  /info            - Get chatbot info")
    print()
    print("🔗 Integration example for your website:")
    print("   const response = await fetch('http://localhost:5001/chat', {")
    print("     method: 'POST',")
    print("     headers: { 'Content-Type': 'application/json' },")
    print("     body: JSON.stringify({ message: 'Plan a trip to Paris' })")
    print("   });")
    print()
    
    # Get port from environment or default to 5001
    port = int(os.environ.get('PORT', 5001))
    
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)