#!/usr/bin/env python3
"""
Simple test server for the chatbot API
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import time

app = Flask(__name__)
CORS(app)

# Simple in-memory storage for sessions
sessions = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': time.time(),
        'service': 'Tripy Travel Chatbot API'
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        session_id = data.get('session_id', 'default')
        
        # Initialize session if not exists
        if session_id not in sessions:
            sessions[session_id] = []
        
        # Add user message to session
        sessions[session_id].append({
            'role': 'user',
            'content': message,
            'timestamp': time.time()
        })
        
        # Generate a simple response based on keywords
        response = generate_response(message)
        
        # Add assistant response to session
        sessions[session_id].append({
            'role': 'assistant', 
            'content': response,
            'timestamp': time.time()
        })
        
        return jsonify({
            'response': response,
            'session_id': session_id,
            'timestamp': time.time()
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'message': 'Failed to process chat request'
        }), 500

@app.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id):
    """Get session history"""
    if session_id in sessions:
        return jsonify({
            'session_id': session_id,
            'messages': sessions[session_id]
        })
    else:
        return jsonify({
            'session_id': session_id,
            'messages': []
        })

@app.route('/info', methods=['GET'])
def get_info():
    """Get API info"""
    return jsonify({
        'name': 'Tripy Travel Chatbot',
        'version': '1.0.0',
        'description': 'AI-powered travel planning assistant',
        'endpoints': ['/health', '/chat', '/sessions/<id>', '/info'],
        'active_sessions': len(sessions)
    })

def generate_response(message):
    """Generate a simple response based on message content"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
        return "Hello! I'm Tripy, your AI travel assistant! 🌍 I can help you plan amazing trips, find destinations, suggest activities, and answer travel questions. Where would you like to go?"
    
    elif any(word in message_lower for word in ['trip', 'travel', 'vacation', 'holiday']):
        return "Great! I'd love to help you plan your trip! ✈️ To give you the best recommendations, could you tell me:\n\n• Where are you thinking of traveling?\n• What time of year?\n• What type of activities interest you?\n• What's your budget range?"
    
    elif any(word in message_lower for word in ['destination', 'where', 'place']):
        return "There are so many amazing destinations to explore! 🗺️ Some popular options include:\n\n• **Europe**: Paris, Rome, Barcelona, Amsterdam\n• **Asia**: Tokyo, Bali, Thailand, Singapore\n• **Americas**: New York, Costa Rica, Peru, Canada\n\nWhat type of experience are you looking for - cultural, adventure, relaxation, or food?"
    
    elif any(word in message_lower for word in ['hotel', 'accommodation', 'stay']):
        return "I can help you find great places to stay! 🏨 Here are some tips:\n\n• **Budget**: Hostels, guesthouses, budget hotels\n• **Mid-range**: 3-4 star hotels, boutique properties\n• **Luxury**: 5-star resorts, premium locations\n\nWhat's your preferred style and budget for accommodation?"
    
    elif any(word in message_lower for word in ['food', 'restaurant', 'eat', 'cuisine']):
        return "Food is one of the best parts of traveling! 🍽️ I can recommend:\n\n• Local specialties to try\n• Popular restaurants and cafes\n• Street food markets\n• Cooking classes and food tours\n\nWhat type of cuisine interests you most?"
    
    elif any(word in message_lower for word in ['activity', 'things to do', 'attractions']):
        return "There are endless activities to enjoy! 🎯 Popular options include:\n\n• **Cultural**: Museums, historical sites, local tours\n• **Adventure**: Hiking, water sports, extreme activities\n• **Relaxation**: Spas, beaches, scenic viewpoints\n• **Entertainment**: Shows, nightlife, festivals\n\nWhat type of activities appeal to you?"
    
    elif any(word in message_lower for word in ['budget', 'cost', 'price', 'expensive']):
        return "Smart budgeting makes trips more enjoyable! 💰 Consider these cost factors:\n\n• **Accommodation**: 30-40% of budget\n• **Food**: 20-30% of budget\n• **Transportation**: 15-25% of budget\n• **Activities**: 15-20% of budget\n\nWhat's your approximate total budget for the trip?"
    
    elif any(word in message_lower for word in ['weather', 'climate', 'season']):
        return "Weather can make or break a trip! 🌤️ Here's what to consider:\n\n• **Spring**: Mild temperatures, fewer crowds\n• **Summer**: Peak season, warm weather\n• **Fall**: Beautiful colors, moderate temps\n• **Winter**: Lower prices, unique experiences\n\nWhat time of year are you planning to travel?"
    
    elif any(word in message_lower for word in ['thank', 'thanks', 'appreciate']):
        return "You're very welcome! 😊 I'm here to help make your travel dreams come true. Feel free to ask me anything else about your trip planning!"
    
    else:
        return f"Thanks for your message! 🌟 I'm here to help with all your travel planning needs. Whether you're looking for destinations, activities, accommodations, or travel tips, I've got you covered! Could you tell me more about what specific aspect of travel you'd like help with?"

if __name__ == '__main__':
    print("🚀 Starting Tripy Travel Chatbot API...")
    print("📍 Health check: http://localhost:5001/health")
    print("💬 Chat endpoint: http://localhost:5001/chat")
    print("📊 API info: http://localhost:5001/info")
    app.run(host='0.0.0.0', port=5001, debug=True)