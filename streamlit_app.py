import streamlit as st
from dataclasses import dataclass
from typing import Literal
import os
from dotenv import load_dotenv

# Import your chatbot functions
from main import get_travel_agent, get_system_prompt
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv(dotenv_path="./config/.env")

@dataclass
class Message:
    origin: Literal["human", "assistant"]
    message: str

def initialize_chatbot():
    """Initialize the travel agent and memory (only once per session)"""
    # This function is now integrated into initialize_session_state()
    pass

def get_chatbot_response(user_input: str) -> str:
    """Get response from your travel chatbot"""
    try:
        # Get conversation history from memory
        history = st.session_state.memory.chat_memory.messages
        
        # Create the full conversation context
        messages = [SystemMessage(content=st.session_state.system_prompt)]
        messages.extend(history)  # Add stored conversation history
        messages.append(HumanMessage(content=user_input))  # Add current input
        
        # Get response from travel agent (using invoke method like your main.py)
        response = st.session_state.travel_agent.invoke(messages)
        
        # Save this exchange to memory
        st.session_state.memory.save_context(
            {"input": user_input}, 
            {"output": response.content}
        )
        
        return response.content
        
    except Exception as e:
        return f"Sorry, I encountered an error: {e}. Please try again!"

def on_click_callback():
    """Handle when user sends a message"""
    human_prompt = st.session_state.human_prompt
    
    if human_prompt.strip():  # Only process non-empty messages
        # Add human message to history
        st.session_state.history.append(
            Message(origin="human", message=human_prompt)
        )
        
        # Get chatbot response
        bot_response = get_chatbot_response(human_prompt)
        
        # Add bot response to history
        st.session_state.history.append(
            Message(origin="assistant", message=bot_response)
        )
        
        # Clear the input box
        st.session_state.human_prompt = ""

def initialize_session_state():
    """Initialize session state variables"""
    # Initialize chatbot FIRST
    if "travel_agent" not in st.session_state:
        st.session_state.travel_agent, st.session_state.memory = get_travel_agent()
        st.session_state.system_prompt = get_system_prompt()
    
    # Then initialize chat history
    if "history" not in st.session_state:
        st.session_state.history = [
            Message(
                origin="assistant", 
                message="Hi! I'm Tripy, your personal travel planning assistant. Tell me where you'd like to go and I'll help plan your perfect trip!"
            )
        ]

def display_message(message: Message):
    """Display a single message with proper styling"""
    if message.origin == "human":
        with st.chat_message("user"):
            st.write(message.message)
    else:
        with st.chat_message("assistant"):
            st.write(message.message)


def main():
    st.set_page_config(
        page_title="Tripy - Smart Trip Planner",
        page_icon=":airplane:",
        layout="wide"
    )
    
    initialize_session_state()
    
    st.title("Welcome to Tripy")
    
    # Chat container
    chat_placeholder = st.container()
    
    # Display chat history
    with chat_placeholder:
        for message in st.session_state.history:
            display_message(message)


    with st.form("prompt_form", clear_on_submit=True):
        cols = st.columns([6, 1])
        
        # Use text_area instead of text_input for multiline support
        user_input = cols[0].text_area(
            "Ask me anything about your trip...", 
            placeholder="e.g., Plan a 4-day trip to Paris for $2000",
            label_visibility="collapsed", 
            key="human_prompt",
            height=70,
            help="💡 Tip: Use Shift+Enter for new lines, Ctrl+Enter to send"
        )
        
        # Submit button
        submitted = cols[1].form_submit_button(
            "Send", 
            type="primary"
        )
        
        # Handle submission
        if submitted and user_input.strip():
            # Adding user message to history
            st.session_state.history.append(
                Message(origin="human", message=user_input.strip())
            )
            
            # Get chatbot response
            bot_response = get_chatbot_response(user_input.strip())
            
            # Addding chatbot response to history
            st.session_state.history.append(
                Message(origin="assistant", message=bot_response)
            )
            
            # Rerun to clear the form and show new messages
            st.rerun()
           
    
    # Sidebar with app info
    with st.sidebar:
        st.markdown("### 🔥Features")
        st.markdown("""
        - **Smart Itineraries**: Day-by-day planning
        - **Budget Planning**: Cost-aware recommendations  
        - **Conversation Memory**: Remembers your preferences
        - **Travel Expertise**: Powered by GPT-4
        """)
        
        st.markdown("### 💡Try asking:")
        st.markdown("""
        - "Plan a weekend in New York for $800"
        - "I want to visit Tokyo, I love food"
        - "What should I pack for Iceland in winter?"
        """)
        
        # Debug info (optional)
        if st.checkbox("Show debug info"):
            st.write(f"Messages in memory: {len(st.session_state.memory.chat_memory.messages)}")
            st.write(f"Chat history length: {len(st.session_state.history)}")

if __name__ == "__main__":
    main()
