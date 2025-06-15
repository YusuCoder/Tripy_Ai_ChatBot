import streamlit as st
from dataclasses import dataclass
from typing import Literal
import os
from dotenv import load_dotenv

# Importing your chatbot functions
from main import get_travel_agent, get_system_prompt, create_new_chat_session, delete_chat_session, get_all_chat_sessions, get_chat_history_for_session, get_session_history
from langchain_core.messages import HumanMessage, SystemMessage

# Loading environment variables
load_dotenv(dotenv_path="./config/.env")

@dataclass
class Message:
    origin: Literal["human", "assistant"]
    message: str

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
    """Get streaming response from your travel chatbot"""
    try:
        # Create messages with system prompt and chat history
        messages = [SystemMessage(content=st.session_state.system_prompt)]
        
        # Add chat history from database if available
        try:
            session_history = get_session_history(st.session_state.current_session_id)
            if hasattr(session_history, 'messages'):
                messages.extend(session_history.messages)
        except Exception as history_error:
            print(f"Warning: Could not load chat history: {history_error}")
        
        # Add current user input
        messages.append(HumanMessage(content=user_input))

        # Stream response from travel agent
        full_response = ""
        for chunk in st.session_state.travel_agent.stream(messages):
            if hasattr(chunk, 'content') and chunk.content:
                full_response += chunk.content
                yield chunk.content
        
        # After streaming, properly save the conversation to database
        # Use the invoke method with proper message structure to ensure persistence
        try:
            # The invoke method will handle saving to the database automatically
            # when using session-based history
            response = st.session_state.travel_agent.invoke([HumanMessage(content=user_input)])
            print(f"Conversation saved successfully for session: {st.session_state.current_session_id}")
        except Exception as save_error:
            print(f"Warning: Could not save conversation: {save_error}")
            # Try alternative approach - directly save to session history
            try:
                session_history = get_session_history(st.session_state.current_session_id)
                session_history.add_user_message(user_input)
                session_history.add_ai_message(full_response)
                print("Chat save method successful")
            except Exception as alt_save_error:
                print(f"Chat save method failed: {alt_save_error}")
        
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
        
        # Set flag to generate response
        st.session_state.awaiting_response = True
        st.session_state.current_user_input = human_prompt

def initialize_session_state():
    """Initialize session state variables"""

    # Loading chat history from database
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = create_new_chat_session()
    
    if "history" not in st.session_state or st.session_state.get("last_loaded_session_id") != st.session_state.current_session_id:
        db_history = get_chat_history_for_session(st.session_state.current_session_id)

        if db_history:
            st.session_state.history = []
            for msg in db_history:
                origin = "human" if msg["origin"] == "human" else "assistant"
                st.session_state.history.append(
                    Message(origin=origin, message=msg["content"])  # Fixed: was msg("content")
                )
        else:
            st.session_state.history = [
                Message(origin="assistant", message="Hi! I'm Tripy, your personal travel planning assistant. Tell me where you'd like to go and I'll help plan your perfect trip!")
            ]
        st.session_state.last_loaded_session_id = st.session_state.current_session_id  # Fixed: was last_loaded_session

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

# Function to switch sessions
def switch_session(session_id: str):
    """Switch to a different chat session"""
    st.session_state.current_session_id = session_id
    # Clearing current agent to force re-initialization with a new session
    if "travel_agent" in st.session_state:
        del st.session_state.travel_agent
    if "memory" in st.session_state:
        del st.session_state.memory
    # Triggering history reload in initialize_session_state
    if "last_loaded_session_id" in st.session_state:
        del st.session_state.last_loaded_session_id

def main():
    st.set_page_config(
        page_title="Tripy - Smart Trip Planner",
        page_icon="✈️",
        layout="wide"
    )
    
    initialize_session_state()
    
    # Sidebar for session switching
    with st.sidebar:
        st.title("Chat Sessions")

        # New session btn
        if st.button("New Chat", use_container_width=True):
            new_session = create_new_chat_session()
            switch_session(new_session)
            st.rerun()
        
        all_sessions = get_all_chat_sessions()

        if all_sessions:
            st.subheader("Active Sessions")
            for i, session in enumerate(all_sessions):  # Fixed: was sessions
                col1, col2 = st.columns([3, 1])

                with col1:
                    display_name = f"Chat {i+1}"
                    is_current = session == st.session_state.current_session_id

                    if st.button(display_name, key=f"chat_{session}", use_container_width=True, type="primary" if is_current else "secondary"):
                        if not is_current:
                            switch_session(session)
                            st.rerun()
                with col2:
                    if st.button("🗑️", key=f"delete_{session}", help="Delete chat"):
                        if delete_chat_session(session):
                            # If I delete the current session, switch to a new session
                            if st.session_state.current_session_id == session:
                                new_session = create_new_chat_session()
                                switch_session(new_session)
                            st.rerun()
        st.markdown("---")

        st.markdown("### 🔥 Features")
        st.markdown("""
        - **Smart Itineraries**: Day-by-day planning
        - **Budget Planning**: Cost-aware recommendations  
        - **Conversation Memory**: Remembers your preferences
        - **Travel Expertise**: Powered by GPT-4
        """)
        
        st.markdown("### 💡 Try asking:")
        st.markdown("""
        - "Plan a weekend in New York for $800"
        - "I want to visit Tokyo, I love food"
        - "What should I pack for Iceland in winter?"
        """)
        
        # Debug info (optional)
        if st.checkbox("Show debug info"):
            # Fixed: Check if memory exists and has the right structure
            memory_count = 0
            if st.session_state.memory and hasattr(st.session_state.memory, 'chat_memory') and hasattr(st.session_state.memory.chat_memory, 'messages'):
                memory_count = len(st.session_state.memory.chat_memory.messages)
            
            st.write(f"Messages in memory: {memory_count}")
            st.write(f"Chat history length: {len(st.session_state.history)}")
            st.write(f"Total sessions: {len(all_sessions) if all_sessions else 0}")
            st.write(f"Current session: {st.session_state.current_session_id[:8]}...")
            
    col1, col2 = st.columns([4, 1])

    with col1:
        # Title and header with custom styling
        st.markdown(
            """
            <h1 style='text-align: center; margin-bottom: 0.5rem;'>🌏 Welcome to Tripy</h1>
            """,
            unsafe_allow_html=True
        )
        # Current session info
        # st.info(f"Current Chat Session: {st.session_state.current_session_id[:8]}...")

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
                        response_placeholder.write(full_response + "▌")  # Cursor effect

                    response_placeholder.markdown(full_response)

                    st.session_state.history.append(
                        Message(origin="assistant", message=full_response)
                    )

                    st.session_state.awaiting_response = False
                    st.session_state.current_user_input = ""

                    st.rerun()  # Rerun to update chat history

        # Custom CSS for styling
        st.markdown("""
            <style>
                .stForm {
                    position: relative;
                }

                .stForm > div:last-child {
                    display: flex;
                    justify-content: flex-end;
                    margin-top: 0.2rem;
                }

                .stForm button {
                    border-radius: 20px;
                    padding: 0.5rem 1.5rem;
                    font-weight: 600;
                }

                /* Make text area container relative for positioning */
                .stTextArea {
                    margin-bottom: 0.2rem;
                }
            </style>
            """, unsafe_allow_html=True)

        # Input form
        with st.form("prompt_form", clear_on_submit=True):
            user_input = st.text_area(
                "Ask me anything about your trip...", 
                placeholder="e.g., Plan a 4-day trip to Paris for €2000",
                label_visibility="collapsed", 
                key="human_prompt",
                height=70,
                help="Tip: Use Shift+Enter for new lines, Ctrl+Enter to send"
            )

            # Create columns for button positioning
            col1, col2, col3 = st.columns([3, 1, 1])
            with col3:
                submitted = st.form_submit_button(
                    "Send ➤", 
                    type="primary",
                    on_click=on_click_callback
                )

if __name__ == "__main__":
    main()


# import streamlit as st
# from dataclasses import dataclass
# from typing import Literal
# import os
# from dotenv import load_dotenv

# # Importing your chatbot functions
# from main import get_travel_agent, get_system_prompt, create_new_chat_session, delete_chat_session, get_all_chat_sessions, get_chat_history_for_session, get_session_history
# from langchain_core.messages import HumanMessage, SystemMessage

# # Loading environment variables
# load_dotenv(dotenv_path="./config/.env")

# @dataclass
# class Message:
#     origin: Literal["human", "assistant"]
#     message: str

# def initialize_chatbot():
#     """Initialize the travel agent and memory (only once per session)"""
#     if "travel_agent" not in st.session_state:
#         # Creating or getting session ID
#         if "current_session_id" not in st.session_state:
#             st.session_state.current_session_id = create_new_chat_session()

#         st.session_state.travel_agent, st.session_state.memory = get_travel_agent()
#         st.session_state.system_prompt = get_system_prompt()

# def get_chatbot_response_stream(user_input: str):
#     """Get streaming response from your travel chatbot"""
#     try:

#         messagess = [SystemMessage(content=st.session_state.system_prompt)]
#         messagess.append(HumanMessage(content=user_input))


#         full_response = ""
#         for chunk in st.session_state.travel_agent.stream(messagess):
#             if hasattr(chunk, 'content') and chunk.content:
#                 full_response += chunk.content
#                 yield chunk.content
        
#         st.session_state.trave_agent.invoke(user_input)

#         # # Getting conversation history from memory
#         # history = st.session_state.memory.chat_memory.messages
        
#         # # Creating the full conversation context
#         # messages = [SystemMessage(content=st.session_state.system_prompt)]
#         # messages.extend(history)  # Add stored conversation history
#         # messages.append(HumanMessage(content=user_input))  # Add current input
        
#         # # Streaming response from travel agent
#         # full_response = ""
#         # for chunk in st.session_state.travel_agent.stream(messages):
#         #     if hasattr(chunk, 'content') and chunk.content:
#         #         full_response += chunk.content
#         #         yield chunk.content
        
#         # # Saving this exchange to memory after streaming is complete
#         # st.session_state.memory.save_context(
#         #     {"input": user_input}, 
#         #     {"output": full_response}
#         # )
        
#         # # Storing the complete response for display history
#         return full_response
        
#     except Exception as e:
#         error_msg = f"Sorry, I encountered an error: {e}. Please try again!"
#         yield error_msg
#         return error_msg

# def on_click_callback():
#     """Handle when user sends a message"""
#     human_prompt = st.session_state.human_prompt
    
#     if human_prompt.strip():  # Only process non-empty messages
#         # Adding human message to history
#         st.session_state.history.append(
#             Message(origin="human", message=human_prompt)
#         )
        
#         # Adding placeholder for bot response (will be updated)

#         st.session_state.awaiting_response = True
#         st.session_state.current_user_input = human_prompt
#         # st.session_state.history.append(
#         #     Message(origin="assistant", message="")
#         # )
        
#         # # Triggering rerun to show the user message immediately
#         # st.rerun()

# def initialize_session_state():
#     """Initialize session state variables"""

#     #Loading chat history from database
#     if "current_session_id" not in st.session_state:
#         st.session_state.current_session_id = create_new_chat_session()
    

#     if "history" not in st.session_state or st.session_state.get("last_loaded_session_id") != st.session_state.current_session_id:
#         db_history = get_chat_history_for_session(st.session_state.current_session_id)

#         if db_history:
#             st.session_state.history = []
#             for msg in db_history:
#                 origin = "human" if msg["origin"] == "human" else "assistant"
#                 st.session_state.history.append = (
#                     Message(origin=origin, message=msg("content"))
#                 )
#         else:
#             st.session_state.history = [
#                 Message(origin="assistant", message="Hi! I'm Tripy, your personal travel planning assistant. Tell me where you'd like to go and I'll help plan your perfect trip!")
#             ]
#         st.session_state.last_loaded_session = st.session_state.current_session_id

#     if "awaiting_response" not in st.session_state:
#         st.session_state.awaiting_response = False
    
#     if "current_user_input" not in st.session_state:
#         st.session_state.current_user_input = ""
    
#     # Initializing chatbot
#     initialize_chatbot()

# def display_message(message: Message):
#     """Display a single message with proper styling"""
#     if message.origin == "human":
#         with st.chat_message("user"):
#             st.write(message.message)
#     else:
#         with st.chat_message("assistant"):
#             st.write(message.message)

# #Function to switch sessions
# def switch_session(session_id: str):
#     """Switch to a different chat session"""
#     st.session_state.current_session_id = session_id
#     # Clearing current agent to forece re-initialization with a new session
#     if "travel_agent" in st.session_state:
#         del st.session_state.travel_agent
#     if "memory" in st.session_state:
#         del st.session_state.memory
#     # Triggering history reload in initilize_session_state
#     if "last_loaded_session" in st.session_state:
#         del st.session_state.last_loaded_session

# def main():
#     st.set_page_config(
#         page_title="Tripy - Smart Trip Planner",
#         page_icon=":airplane:",
#         layout="wide"
#     )
    
#     initialize_session_state()
    
#     # Sidebar for session switching

#     with st.sidebar:
#         st.title("Chat Sessions")

#         #New session btn
#         if st.button("New Chat", use_container_width=True):
#             new_session = create_new_chat_session()
#             switch_session(new_session)
#             st.rerun()
        
#         all_sessions = get_all_chat_sessions()

#         if all_sessions:
#             st.subheader("Active Sessions")
#             for i, sessions in enumerate(all_sessions):
#                 col1, col2 = st.columns([3, 1])

#                 with col1:

#                     display_name = f"Chat {i+1}"
#                     is_current = sessions == st.session_state.current_session_id

#                     if st.button(display_name, key=f"chat_{sessions}", use_container_width=True, type="primary" if is_current else "secondary"):
#                         if not is_current:
#                             switch_session(sessions)
#                             st.rerun()
#                 with col2:
#                     if st.button("Delete", key=f"delete_{sessions}", help="Delete chat"):
#                         if delete_chat_session(sessions):
#                             #If i delete the currents session, switch to the new session
#                             if st.session_state.current_session_id == sessions:
#                                 new_session = create_new_chat_session()
#                                 switch_session(new_session)
#                             st.rerun()
#         st.markdown("---")

#         st.markdown("### 🔥Features")
#         st.markdown("""
#         - **Smart Itineraries**: Day-by-day planning
#         - **Budget Planning**: Cost-aware recommendations  
#         - **Conversation Memory**: Remembers your preferences
#         - **Travel Expertise**: Powered by GPT-4
#         """)
        
#         st.markdown("### 💡Try asking:")
#         st.markdown("""
#         - "Plan a weekend in New York for $800"
#         - "I want to visit Tokyo, I love food"
#         - "What should I pack for Iceland in winter?"
#         """)
        
#         # Debug info (optional)
#         if st.checkbox("Show debug info"):
#             st.write(f"Messages in memory: {len(st.session_state.memory.chat_memory.messages)}")
#             st.write(f"Chat history length: {len(st.session_state.history)}")
#             st.write(f"Total sessions: {len(all_sessions)}")
#             st.write(f"Chat history length: {len(st.session_state.history)}")
            
#     col1, col2 = st.columns([4, 1])

#     with col1:
#         # Title and header with custom styling
#         st.markdown(
#             """
#             <h1 style='text-align: center; margin-bottom: 0.5rem;'>🌏  Welcome to Tripy</h1>
#             """,
#             unsafe_allow_html=True
#         )
#         #Current session info
#         st.info(f"Current Chat Session: {st.session_state.current_session_id[:8]}...")

#         # Chat container
#         chat_placeholder = st.container()

#         # Displaying chat history
#         with chat_placeholder:
#             for message in st.session_state.history:
#                 if message.origin == "human":
#                     with st.chat_message("user"):
#                         st.write(message.message)
#                 else:
#                     with st.chat_message("assistant"):
#                         st.write(message.message)

#             if st.session_state.awaiting_response:    
#                 with st.chat_message("assistant"):
#                         response_placeholder = st.empty()
#                         full_response = ""

#                         for chunk in get_chatbot_response_stream(st.session_state.current_user_input):
#                             full_response += chunk
#                             response_placeholder.write(full_response + "▌")  # Cursor effect

#                         response_placeholder.markdown(full_response)

#                         st.session_state.history.append(
#                             Message(origin="assistant", message=full_response)
#                         )

#                         st.session_state.awaiting_response = False
#                         st.session_state.current_user_input = ""

#                         st.rerun()  # Rerun to update chat history

#         # Custom CSS for styling
#         st.markdown("""
#             <style>
#                 .stForm {
#                     position: relative;
#                 }

#                 .stForm > div:last-child {
#                     display: flex;
#                     justify-content: flex-end;
#                     margin-top: 0.2rem;
#                 }

#                 .stForm button {
#                     border-radius: 20px;
#                     padding: 0.5rem 1.5rem;
#                     font-weight: 600;
#                 }

#                 /* Make text area container relative for positioning */
#                 .stTextArea {
#                     margin-bottom: 0.2rem;
#                 }
#             </style>
#             """, unsafe_allow_html=True)

#         # Input form.
#         with st.form("prompt_form", clear_on_submit=True):
#             user_input = st.text_area(
#                 "Ask me anything about your trip...", 
#                 placeholder="e.g., Plan a 4-day trip to Paris for €2000",
#                 label_visibility="collapsed", 
#                 key="human_prompt",
#                 height=70,
#                 help="Tip: Use Shift+Enter for new lines, Ctrl+Enter to send"
#             )

#             # Create columns for button positioning
#             col1, col2, col3 = st.columns([3, 1, 1])
#             with col3:
#                 submitted = st.form_submit_button(
#                     "Send ➤", 
#                     type="primary",
#                     on_click=on_click_callback
#                 )

#     # Sidebar with app info
#     # with st.sidebar:
#     #     st.markdown("### 🔥Features")
#     #     st.markdown("""
#     #     - **Smart Itineraries**: Day-by-day planning
#     #     - **Budget Planning**: Cost-aware recommendations  
#     #     - **Conversation Memory**: Remembers your preferences
#     #     - **Travel Expertise**: Powered by GPT-4
#     #     """)
        
#     #     st.markdown("### 💡Try asking:")
#     #     st.markdown("""
#     #     - "Plan a weekend in New York for $800"
#     #     - "I want to visit Tokyo, I love food"
#     #     - "What should I pack for Iceland in winter?"
#     #     """)
        
#     #     # Debug info (optional)
#     #     if st.checkbox("Show debug info"):
#     #         st.write(f"Messages in memory: {len(st.session_state.memory.chat_memory.messages)}")
#     #         st.write(f"Chat history length: {len(st.session_state.history)}")

# if __name__ == "__main__":
#     main()
