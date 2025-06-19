import streamlit as st
from dotenv import load_dotenv
from prompts.prompt import get_system_prompt
# Importing your chatbot functions
from main import get_travel_agent, create_new_chat_session, get_chat_history_for_session, get_session_history, LANGFUSE_ENABLED
from langchain_core.messages import HumanMessage, SystemMessage
from streamlit_.message_types import Message
import json
import base64

load_dotenv(dotenv_path="./config/.env")

def initialize_chatbot():
    """Initialize the travel agent and memory (only once per session)"""
    if "travel_agent" not in st.session_state or st.session_state.get("agent_session_id") != st.session_state.current_session_id:
        # Creating or getting session ID
        if "current_session_id" not in st.session_state:
            st.session_state.current_session_id = create_new_chat_session()
            
        st.session_state.travel_agent, st.session_state.memory = get_travel_agent(st.session_state.current_session_id)
        st.session_state.system_prompt = get_system_prompt()
        st.session_state.agent_session_id = st.session_state.current_session_id


def get_chatbot_response_stream(user_input: str):
    """Enhanced version with better image context handling"""
    try:
        print(f"🚀 Processing user input: {user_input[:50]}...")
        
        # Check if user is asking about image and enhance context
        latest_labels = st.session_state.get("latest_image_labels", [])
        enhanced_input = user_input
        
        if latest_labels and contains_image_reference(user_input):
            label_names = [label['Name'] for label in latest_labels[:5]]
            enhanced_input = f"""User question: {user_input}

        CONTEXT: The user previously uploaded an image containing: {', '.join(label_names)}. 
        When they refer to "this place", "the image", "this location", they mean the location/elements shown in their uploaded image. Please provide travel advice based on both their question and this image context."""

        # Create messages with system prompt
        messages = [SystemMessage(content=st.session_state.system_prompt)]
        
        # Load chat history (this will include saved image context)
        try:
            session_history = get_session_history(st.session_state.current_session_id)
            if hasattr(session_history, 'messages'):
                messages.extend(session_history.messages)
        except Exception as history_error:
            print(f"⚠️ Warning: Could not load chat history: {history_error}")
        
        # Add current user input (enhanced with image context if needed)
        messages.append(HumanMessage(content=enhanced_input))

        # Stream response
        print(f"🔄 Starting streaming response...")
        full_response = ""
        for chunk in st.session_state.travel_agent.stream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                full_response += chunk.content
                yield chunk.content
        
        print(f"✅ Streaming completed. Response length: {len(full_response)} chars")
        
        # Save conversation to database
        try:
            print(f"💾 Saving conversation to database...")
            # Use the original user input (not enhanced) for saving
            response = st.session_state.travel_agent.invoke([HumanMessage(content=user_input)])
            print(f"✅ Conversation saved successfully")
            
        except Exception as save_error:
            print(f"⚠️ Warning: Could not save conversation: {save_error}")
            try:
                session_history = get_session_history(st.session_state.current_session_id)
                session_history.add_user_message(user_input)
                session_history.add_ai_message(full_response)
                print("✅ Alternative chat save method successful")
            except Exception as alt_save_error:
                print(f"❌ Alternative chat save method failed: {alt_save_error}")
        
        return full_response
        
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {e}. Please try again!"
        print(f"❌ Error in get_chatbot_response_stream: {e}")
        yield error_msg
        return error_msg

def contains_image_reference(text):
    """Enhanced detection of image references"""
    image_refs = [
        "this place", "the image", "this photo", "the picture", "this location", 
        "where is this", "what is this place", "this destination", "the location",
        "about this", "tell me about", "information about", "details about",
        "visit here", "go there", "travel to", "trip to", "plan for this",
        "where was this taken", "what's this location", "recognize this",
        "from the image", "in the picture", "what i uploaded", "the photo i shared",
        "based on the image", "what you see", "from what you can see"
    ]
    text = text.lower()
    return any(ref in text for ref in image_refs)


def on_click_callback():
    """Handle when user sends a message"""
    human_prompt = st.session_state.human_prompt
    
    if human_prompt.strip():  # Only process non-empty messages
        print(f"👤 User message: {human_prompt[:50]}...")
        # Adding human message to history
        st.session_state.history.append(
            Message(origin="human", message=human_prompt)
        )
        
        # Set flag to generate response
        st.session_state.awaiting_response = True
        st.session_state.current_user_input = human_prompt

def initialize_image_storage():
    """Initialize image storage in session state"""
    if "session_images" not in st.session_state:
        st.session_state.session_images = {}


def initialize_session_state():
    """Initialize session state variables"""

    # Loading chat history from database
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = create_new_chat_session()
        print(f"🆕 Created new session: {st.session_state.current_session_id[:8]}...")
    
    if "history" not in st.session_state or st.session_state.get("last_loaded_session_id") != st.session_state.current_session_id:
        print(f"📂 Loading history for session: {st.session_state.current_session_id[:8]}...")
        db_history = get_chat_history_for_session(st.session_state.current_session_id)

        if db_history:
            st.session_state.history = []
            for msg in db_history:
                origin = "human" if msg["origin"] == "human" else "assistant"
                st.session_state.history.append(
                    Message(origin=origin, message=msg["content"])
                )
            print(f"✅ Loaded {len(db_history)} messages from database")
        else:
            st.session_state.history = [
                Message(origin="assistant", message="Hi! I'm Tripy, your personal travel planning assistant. Tell me where you'd like to go and I'll help plan your perfect trip!")
            ]
            print("✅ Initialized with welcome message")
        st.session_state.last_loaded_session_id = st.session_state.current_session_id

    if "awaiting_response" not in st.session_state:
        st.session_state.awaiting_response = False
    
    if "current_user_input" not in st.session_state:
        st.session_state.current_user_input = ""
    
    # Initializing chatbot
    initialize_chatbot()


def display_message(message: Message):
    """Display a single message with proper styling"""
    if message.origin == "human":
        with st.chat_message("user"):
            st.write(message.message)
    else:
        with st.chat_message("assistant"):
            st.write(message.message)


def switch_session(session_id: str):
    """Switch to a different chat session while preserving image context"""
    print(f"🔄 Switching to session: {session_id[:8]}...")
    st.session_state.current_session_id = session_id
    # Clearing current agent to force re-initialization
    if "travel_agent" in st.session_state:
        del st.session_state.travel_agent
    if "memory" in st.session_state:
        del st.session_state.memory
    # Clearing image context when switching sessions
    if "latest_image_labels" in st.session_state:
        del st.session_state.latest_image_labels
    # Trigger history reload
    if "last_loaded_session_id" in st.session_state:
        del st.session_state.last_loaded_session_id

