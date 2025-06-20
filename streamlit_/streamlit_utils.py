import streamlit as st
from dotenv import load_dotenv
from prompts.prompt import get_system_prompt
# Importing your chatbot functions
from main import get_travel_agent, create_new_chat_session, get_chat_history_for_session, get_session_history, LANGFUSE_ENABLED
from langchain_core.messages import HumanMessage, SystemMessage
from streamlit_.message_types import Message
# from flights.flight_details import  extract_travel_details_nlp

load_dotenv(dotenv_path="./config/.env")

# def get_flight_details_from_input(user_input):

#     info = extract_travel_details_nlp(user_input)
#     for key, value in info.items():
#         if value and not st.session_state.get[key]:
#             st.session_state[key] = value
#     print("🧭 Travel Info Collected So Far:")
#     print(info)


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
    """Get streaming response from your travel chatbot with Langfuse tracing"""
    try:
        print(f"Processing user input: {user_input[:50]}...")
        
        # Creating messages with system prompt and chat history
        messages = [SystemMessage(content=st.session_state.system_prompt)]
        
        # Adding chat history from database if available
        try:
            session_history = get_session_history(st.session_state.current_session_id)
            if hasattr(session_history, 'messages'):
                messages.extend(session_history.messages)
        except Exception as history_error:
            print(f"Warning: Could not load chat history: {history_error}")
        
        # Adding current user input
        messages.append(HumanMessage(content=user_input))
        # get_flight_details_from_input(user_input)

        # Stream response from travel agent
        print(f"Starting streaming response...")
        full_response = ""
        for chunk in st.session_state.travel_agent.stream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                full_response += chunk.content
                yield chunk.content
        
        print(f"Streaming completed. Response length: {len(full_response)} chars")
        
        try:
            print(f"Saving conversation to database...")
            # The invoke method will handle saving to the database automatically
            response = st.session_state.travel_agent.invoke([HumanMessage(content=user_input)])
            print(f"Conversation saved successfully for session: {st.session_state.current_session_id[:8]}...")
            
            # Log to Langfuse if enabled
            if LANGFUSE_ENABLED:
                print(f"Langfuse tracing is enabled - traces should appear in dashboard")
            else:
                print(f"Langfuse tracing is disabled")
                
        except Exception as save_error:
            print(f"Warning: Could not save conversation: {save_error}")
            # Try alternative approach - directly save to session history
            try:
                session_history = get_session_history(st.session_state.current_session_id)
                session_history.add_user_message(user_input)
                session_history.add_ai_message(full_response)
                print("Alternative chat save method successful")
            except Exception as alt_save_error:
                print(f"❌ Alternative chat save method failed: {alt_save_error}")
        
        return full_response
        
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {e}. Please try again!"
        print(f"❌ Error in get_chatbot_response_stream: {e}")
        yield error_msg
        return error_msg

def on_click_callback():
    """Handle when user sends a message (original callback for backward compatibility)"""
    human_prompt = st.session_state.human_prompt
    
    if human_prompt.strip():  # Only process non-empty messages
        print(f"User message: {human_prompt[:50]}...")
        # Adding human message to history
        st.session_state.history.append(
            Message(origin="human", message=human_prompt)
        )
        
        # Set flag to generate response
        st.session_state.awaiting_response = True
        st.session_state.current_user_input = human_prompt

def initialize_session_state():
    """Initialize session state variables"""

    # Loading chat history from database
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = create_new_chat_session()
        print(f"Created new session: {st.session_state.current_session_id[:8]}...")
    
    if "history" not in st.session_state or st.session_state.get("last_loaded_session_id") != st.session_state.current_session_id:
        print(f"Loading history for session: {st.session_state.current_session_id[:8]}...")
        db_history = get_chat_history_for_session(st.session_state.current_session_id)

        if db_history:
            st.session_state.history = []
            for msg in db_history:
                origin = "human" if msg["origin"] == "human" else "assistant"
                st.session_state.history.append(
                    Message(origin=origin, message=msg["content"])
                )
            print(f"Loaded {len(db_history)} messages from database")
        else:
            st.session_state.history = [
                Message(origin="assistant", message="Hi! I'm Tripy, your personal travel planning assistant. Tell me where you'd like to go and I'll help plan your perfect trip! You can also upload images of places you'd like to know more about.")
            ]
            print("Initialized with welcome message")
        st.session_state.last_loaded_session_id = st.session_state.current_session_id

    if "awaiting_response" not in st.session_state:
        st.session_state.awaiting_response = False
    
    if "current_user_input" not in st.session_state:
        st.session_state.current_user_input = ""
    
    if "current_image" not in st.session_state:
        st.session_state.current_image = None
    
    # Initializing chatbot
    initialize_chatbot()

def switch_session(session_id: str):
    """Switch to a different chat session"""
    print(f"Switching to session: {session_id[:8]}...")
    st.session_state.current_session_id = session_id
    # Clearing current agent to force re-initialization with a new session
    if "travel_agent" in st.session_state:
        del st.session_state.travel_agent
    if "memory" in st.session_state:
        del st.session_state.memory
    # Triggering history reload in initialize_session_state
    if "last_loaded_session_id" in st.session_state:
        del st.session_state.last_loaded_session_id
