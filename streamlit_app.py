import streamlit as st
from dataclasses import dataclass
from typing import Literal
import os
from dotenv import load_dotenv
import base64
from io import BytesIO
from PIL import Image
# Importing your chatbot functions
from langchain_core.messages import HumanMessage, SystemMessage
from streamlit_.message_types import Message
from google.cloud import vision
import base64
import time
from main import (
    create_new_chat_session, 
    delete_chat_session, 
    get_all_chat_sessions, 
    get_chat_history_for_session, 
    get_session_history, 
    LANGFUSE_ENABLED
)
from streamlit_.streamlit_utils import (
    get_chatbot_response_stream,
    on_click_callback,
    initialize_session_state,
    switch_session
)

load_dotenv(dotenv_path="./config/.env")
client = vision.ImageAnnotatorClient()

def process_image_with_vision(image_file):
    """Process uploaded image with Google Vision API to detect landmarks"""
    try:
        image_content = image_file.read()
        image_file.seek(0)  # Reseting file pointer for display
        
        image = vision.Image(content=image_content)
        
        landmark_response = client.landmark_detection(image=image)
        landmarks = []
        for landmark in landmark_response.landmark_annotations:
            landmarks.append({
                'name': landmark.description,
                'confidence': landmark.score if hasattr(landmark, 'score') else 0.0
            })
        
        # Detecting some text from the picture for signs, etc.
        text_response = client.text_detection(image=image)
        detected_text = text_response.text_annotations[0].description if text_response.text_annotations else ""
        
        #Detecting object labels
        label_response = client.label_detection(image=image)
        labels = []
        for label in label_response.label_annotations[:5]:
            labels.append({
                'name': label.description,
                'confidence': label.score
            })
        
        return {
            'landmarks': landmarks,
            'text': detected_text.strip() if detected_text else "",
            'labels': labels,
            'success': True
        }
    except Exception as e:
        print(f"Error processing image with Vision API: {e}")
        return {
            'landmarks': [],
            'text': "",
            'labels': [],
            'success': False,
            'error': str(e)
        }

def create_vision_prompt(vision_data, user_text=""):
    """Create a comprehensive prompt combining user text and vision analysis"""

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
        
        prompt_parts.append("Please provide detailed information about this place, where is this place located, if not exact one landmark provided, give the information about the street, including travel tips, best times to visit, nearby attractions, and any other relevant travel advice.")
    else:
        prompt_parts.append("I uploaded an image but there was an issue processing it. Please help me with my travel question.")
    
    return "\n\n".join(prompt_parts)

def render_input_form():
    """Render the input form for user queries and image uploads"""
    if 'uploaded_image' not in st.session_state:
        st.session_state.uploaded_image = None
    if 'show_upload' not in st.session_state:
        st.session_state.show_upload = False
    if 'processing' not in st.session_state:
        st.session_state.processing = False

    st.markdown("""
    <style>
    .plus-button {
        background-color: #ff6b6b;
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        font-size: 20px;
        font-weight: bold;
        cursor: pointer;
        transition: background-color 0.3s;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .plus-button:hover {
        background-color: #ff5252;
    }
    .hidden-upload {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.session_state.show_upload:
        uploaded_file = st.file_uploader(
            "Choose an image",
            type=["jpg", "jpeg", "png"],
            key="file_upload_modal"
        )
        if uploaded_file is not None:
            st.session_state.uploaded_image = uploaded_file
            st.session_state.show_upload = False
            st.rerun()

    col_pre1, col_pre2 = st.columns([3, 1])
    
    with col_pre1:
        # Plus button to trigger file upload (outside form)
        if st.button("➕", key="plus_btn", help="Add image", disabled=st.session_state.processing):
            st.session_state.show_upload = True
            st.rerun()

    with col_pre2:
        if st.session_state.uploaded_image is not None:
            col2a, col2b, col3 = st.columns([2, 1, 1])
            with col2b:
                st.image(st.session_state.uploaded_image, width=150)
            with col3:
                if st.button("❌", key="remove_img", help="Remove image", disabled=st.session_state.processing):
                    st.session_state.uploaded_image = None
                    st.rerun()

    with st.form("prompt_form", clear_on_submit=True):
        user_input = st.text_area(
            "Ask me anything about your trip...",
            placeholder="e.g., Plan a 4-day trip to Paris for €2000, or upload an image of a place you want to know about",
            label_visibility="collapsed",
            key="human_prompt",
            height=70,
            help="Tip: Use Shift+Enter for new lines, Ctrl+Enter to send",
            disabled=st.session_state.processing
        )

        col1, col2, col3 = st.columns([6, 2, 2])
        with col3:
            submitted = st.form_submit_button(
                "Send ➤",
                type="primary",
                use_container_width=True
            )
        
        # Handle form submission
        if submitted and not st.session_state.processing:
            current_image = st.session_state.uploaded_image
            current_text = user_input
            
            if current_text.strip() or current_image is not None:
                st.session_state.processing = True
                
                try:
                    if current_image is not None:
                        st.session_state.uploaded_image = None
                        on_click_callback_with_image(current_image)
                    else:
                        on_click_callback_with_image(None)
                finally:
                    st.session_state.processing = False
                
                st.rerun()

def on_click_callback_with_image(uploaded_file=None):
    """Enhanced callback that handles both text and image input"""
    human_prompt = st.session_state.human_prompt
    
    # Process image if uploaded
    vision_data = None
    if uploaded_file:
        print(f"Processing uploaded image: {uploaded_file.name}")
        vision_data = process_image_with_vision(uploaded_file)
        
        # Storing image data for display in chat
        image_data = uploaded_file.read()
        uploaded_file.seek(0)
        st.session_state.current_image = {
            'data': image_data,
            'name': uploaded_file.name,
            'type': uploaded_file.type
        }
    else:
        st.session_state.current_image = None
    
    # Createing combined prompt here
    if vision_data or human_prompt.strip():
        if vision_data:
            combined_prompt = create_vision_prompt(vision_data, human_prompt)
        else:
            combined_prompt = human_prompt
        
        print(f"Combined prompt: {combined_prompt[:100]}...")
        
        # Add message to history with image if present
        message_content = human_prompt if human_prompt.strip() else "Uploaded an image for analysis"
        st.session_state.history.append(
            Message(
                origin="human", 
                message=message_content,
                image=st.session_state.current_image if uploaded_file else None
            )
        )
        
        # Seting flag to generate response
        st.session_state.awaiting_response = True
        st.session_state.current_user_input = combined_prompt

def inject_custom_css():
    st.markdown("""
    <style>
    /* Remove file uploader background and borders */
    .stFileUploader > div > div {
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        box-shadow: none !important;
    }

    .stFileUploader > div > div > div {
        background: transparent !important;
        border: none !important;
        min-height: auto !important;
        padding: 0 !important;
    }

    .stFileUploader div[data-testid="stFileUploaderDropzone"] {
        display: none !important;
    }

    /* Style the browse files button */
    .stFileUploader button {
        background-color: #ff6b6b !important;
        color: white !important;
        border: none !important;
        padding: 8px 16px !important;
        border-radius: 6px !important;
        cursor: pointer !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        margin: 0 !important;
    }
    
    .stFileUploader button:hover {
        background-color: #ff5252 !important;
    }

    /* Ensure file uploader container has no background */
    .stFileUploader {
        background: transparent !important;
    }
    
    /* Chat message image styling */
    .chat-image {
        max-width: 300px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

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
            .stTextArea {
                margin-bottom: 0.2rem;
            }
        </style>
    """, unsafe_allow_html=True)

def render_chat():
    chat_placeholder = st.container()
    with chat_placeholder:
        for message in st.session_state.history:
            with st.chat_message("user" if message.origin == "human" else "assistant"):
                if hasattr(message, 'image') and message.image:
                    st.image(
                        message.image['data'], 
                        caption=f"📷 {message.image['name']}", 
                        width=300
                    )
                st.markdown(message.message)
        
        if st.session_state.awaiting_response:
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                buffer = ""
                last_update = time.time()
                
                for chunk in get_chatbot_response_stream(st.session_state.current_user_input):
                    buffer += chunk
                    current_time = time.time()
                    
                    # Update every 80ms or when we hit word boundaries
                    should_update = (
                        current_time - last_update >= 0.1 or 
                        chunk.endswith((' ', '\n', '.', '!', '?', ',')) or
                        len(buffer) >= 15
                    )
                    
                    if should_update:
                        full_response += buffer
                        response_placeholder.markdown(full_response + " ●")
                        buffer = ""
                        last_update = current_time
                        time.sleep(0.02)  # Small pause for smoothness
                
                # Handle any remaining buffer
                if buffer:
                    full_response += buffer
                
                # Final clean update
                response_placeholder.markdown(full_response)
                st.session_state.history.append(Message(origin="assistant", message=full_response))
                st.session_state.awaiting_response = False
                st.session_state.current_user_input = ""
                st.session_state.current_image = None 
                st.rerun()


# def render_chat():
#     chat_placeholder = st.container()
#     with chat_placeholder:
#         for message in st.session_state.history:
#             with st.chat_message("user" if message.origin == "human" else "assistant"):
#                 if hasattr(message, 'image') and message.image:
#                     st.image(
#                         message.image['data'], 
#                         caption=f"📷 {message.image['name']}", 
#                         width=300
#                     )
#                 st.write(message.message)
        
#         if st.session_state.awaiting_response:
#             with st.chat_message("assistant"):
#                 response_placeholder = st.empty()
#                 full_response = ""
#                 for chunk in get_chatbot_response_stream(st.session_state.current_user_input):
#                     full_response += chunk
#                     response_placeholder.write(full_response + "▌")
#                 response_placeholder.markdown(full_response)
#                 st.session_state.history.append(Message(origin="assistant", message=full_response))
#                 st.session_state.awaiting_response = False
#                 st.session_state.current_user_input = ""
#                 st.session_state.current_image = None 
#                 st.rerun()

def render_header():
    st.markdown("<h1 style='text-align: center; margin-bottom: 0.5rem;'>🌏 Welcome to Tripy</h1>", unsafe_allow_html=True)

def setup_main_chat_area():
    col1, col2 = st.columns([4, 1])
    with col1:
        render_header()
        render_chat()
        inject_custom_css()
        render_input_form()

def display_debug_info():
    if st.checkbox("Show debug info"):
        memory_count = 0
        if st.session_state.memory and hasattr(st.session_state.memory, 'chat_memory') and hasattr(st.session_state.memory.chat_memory, 'messages'):
            memory_count = len(st.session_state.memory.chat_memory.messages)
        st.write(f"Messages in memory: {memory_count}")
        st.write(f"Chat history length: {len(st.session_state.history)}")
        st.write(f"Total sessions: {len(get_all_chat_sessions())}")
        st.write(f"Current session: {st.session_state.current_session_id[:8]}...")
        st.write(f"Langfuse enabled: {LANGFUSE_ENABLED}")

def display_feature_tips():
    st.markdown("---")
    st.markdown("### 🔥 Features")
    st.markdown("""
    - **Smart Itineraries**: Day-by-day planning
    - **Budget Planning**: Cost-aware recommendations  
    - **Image Recognition**: Upload photos of places
    - **Conversation Memory**: Remembers your preferences
    - **Travel Expertise**: Powered by GPT-4
    """)
    st.markdown("### 💡 Try asking:")
    st.markdown("""
    - "Plan a weekend in New York for $800"
    - "I want to visit Tokyo, I love food"
    - Upload a photo: "Tell me about this place"
    - "What should I pack for Iceland in winter?"
    """)

def display_chat_session_entry(session, index):
    col1, col2 = st.columns([3, 1])
    with col1:
        display_name = f"Chat {index+1}"
        is_current = session == st.session_state.current_session_id
        if st.button(display_name, key=f"chat_{session}", use_container_width=True, type="primary" if is_current else "secondary"):
            if not is_current:
                switch_session(session)
                st.rerun()
    with col2:
        if st.button("🗑️", key=f"delete_{session}", help="Delete chat"):
            if delete_chat_session(session):
                if st.session_state.current_session_id == session:
                    new_session = create_new_chat_session()
                    switch_session(new_session)
                st.rerun()

def display_session_controls():
    if st.button("New Chat", use_container_width=True):
        new_session = create_new_chat_session()
        switch_session(new_session)
        st.rerun()

    all_sessions = get_all_chat_sessions()
    if all_sessions:
        st.subheader("Active Sessions")
        for i, session in enumerate(all_sessions):
            display_chat_session_entry(session, i)

def display_sidebar_header():
    st.title("Chat Sessions")

def display_langfuse_status():
    if LANGFUSE_ENABLED:
        st.success("Langfuse: Active")
    else:
        st.warning("Langfuse: Disabled")

def setup_sidebar():
    with st.sidebar:
        display_langfuse_status()
        display_sidebar_header()
        display_session_controls()
        display_feature_tips()
        display_debug_info()

def setup_page():
    st.set_page_config(
        page_title="Tripy - Smart Trip Planner",
        page_icon="✈️",
        layout="wide"
    )

def main():
    setup_page()
    initialize_session_state()
    setup_sidebar()
    setup_main_chat_area()

if __name__ == "__main__":
    main()
