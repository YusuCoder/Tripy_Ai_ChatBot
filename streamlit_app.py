import streamlit as st
from dataclasses import dataclass
from typing import Literal
import os
from dotenv import load_dotenv

# Importing your chatbot functions
from main import get_travel_agent, get_system_prompt
from langchain_core.messages import HumanMessage, SystemMessage

# Loading environment variables
load_dotenv(dotenv_path="./config/.env")

@dataclass
class Message:
    origin: Literal["human", "assistant"]
    message: str

def initialize_chatbot():
    """Initialize the travel agent and memory (only once per session)"""
    if "travel_agent" not in st.session_state:
        st.session_state.travel_agent, st.session_state.memory = get_travel_agent()
        st.session_state.system_prompt = get_system_prompt()

def get_chatbot_response_stream(user_input: str):
    """Get streaming response from your travel chatbot"""
    try:
        # Getting conversation history from memory
        history = st.session_state.memory.chat_memory.messages
        
        # Creating the full conversation context
        messages = [SystemMessage(content=st.session_state.system_prompt)]
        messages.extend(history)  # Add stored conversation history
        messages.append(HumanMessage(content=user_input))  # Add current input
        
        # Streaming response from travel agent
        full_response = ""
        for chunk in st.session_state.travel_agent.stream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                full_response += chunk.content
                yield chunk.content
        
        # Saving this exchange to memory after streaming is complete
        st.session_state.memory.save_context(
            {"input": user_input}, 
            {"output": full_response}
        )
        
        # Storing the complete response for display history
        return full_response
        
    except Exception as e:
        error_msg = f"Sorry, I encountered an error: {e}. Please try again!"
        yield error_msg
        return error_msg

def on_click_callback():
    """Handle when user sends a message"""
    human_prompt = st.session_state.human_prompt
    
    if human_prompt.strip():  # Only process non-empty messages
        # Adding human message to history
        st.session_state.history.append(
            Message(origin="human", message=human_prompt)
        )
        
        # Adding placeholder for bot response (will be updated)

        st.session_state.awaiting_response = True
        st.session_state.current_user_input = human_prompt
        # st.session_state.history.append(
        #     Message(origin="assistant", message="")
        # )
        
        # # Triggering rerun to show the user message immediately
        # st.rerun()

def initialize_session_state():
    """Initialize session state variables"""
    if "history" not in st.session_state:
        st.session_state.history = [
            Message(
                origin="assistant", 
                message="Hi! I'm TripBot, your personal travel planning assistant. Tell me where you'd like to go and I'll help plan your perfect trip!"
            )
        ]

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

def main():
    st.set_page_config(
        page_title="Tripy - Smart Trip Planner",
        page_icon=":airplane:",
        layout="wide"
    )

    #CSS for custom styling
    st.markdown("""
    <style>
    .stForm {
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)
    

    initialize_session_state()
    
    st.title("Welcome to Tripy")
    
    # Chat container
    chat_placeholder = st.container()
    
    # Displaying chat history
    with chat_placeholder:
        for message in st.session_state.history:
            if message.origin == "human":
                with st.chat_message("user"):
                    st.write(message.message)
            else:
                with st.chat_message("assistant"):
                    st.write(message.message)
                
        if st.session_state.awaiting_response:    
            with st.chat_message("assistant"):
                    response_placeholder = st.empty()
                    full_response = ""
                    
                    for chunk in get_chatbot_response_stream(st.session_state.current_user_input):
                        full_response += chunk
                        response_placeholder.write(full_response + "▌") 
                    
                    response_placeholder.markdown(full_response)

                    st.session_state.history.append(
                        Message(origin="assistant", message=full_response)
                    )

                    st.session_state.awaiting_response = False
                    st.session_state.current_user_input = ""

                    st.rerun()  # Rerun to update chat history
                    

    # Input form
    with st.form("prompt_form", clear_on_submit=True):
        cols = st.columns([8, 1])  # 8 parts for text area, 1 part for button

        with cols[0]:
            user_input = st.text_area(
                "Ask me anything about your trip...", 
                placeholder="e.g., Plan a 4-day trip to Paris for $2000",
                label_visibility="collapsed", 
                key="human_prompt",
                height=70
            )

        with cols[1]:
            # Add spacing to vertically center the button
            st.write("")
            st.write("")  # Empty space
            submitted = st.form_submit_button(
                " ➤ Send", 
                type="primary", 
                on_click=on_click_callback,
            )

    
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
