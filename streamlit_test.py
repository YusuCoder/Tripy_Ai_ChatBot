import streamlit as st
from dataclasses import dataclass
from typing import Literal
import os
from dotenv import load_dotenv
# Importing your chatbot functions
from langchain_core.messages import HumanMessage, SystemMessage
from streamlit_.message_types import Message
from aws.i_recognition import detect_image

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
    display_message,
    switch_session
)

# Loading environment variables
load_dotenv(dotenv_path="./config/.env")


def get_latest_image_labels():
    return st.session_state.get("latest_image_labels", [])


def handle_image_upload():
    st.subheader("Upload an Image")

def contains_image_reference(text):
    """Detect if user is referring to a previously uploaded image"""
    image_refs = [
        "this place", "the image", "this photo", "the picture", "this location", 
        "where is this", "what is this place", "this destination", "the location",
        "about this", "tell me about", "information about", "details about",
        "visit here", "go there", "travel to", "trip to", "plan for this",
        "where was this taken", "what's this location", "recognize this"
    ]
    text = text.lower()
    return any(ref in text for ref in image_refs)

def get_enhanced_input_with_image_context(user_input, latest_labels):
    """Enhanced logic to add image context to user input"""
    if not latest_labels:
        return user_input

     # Create labels summary with confidence scores
    labels_with_confidence = [f"{label['Name']} ({label['Confidence']:.1f}%)" for label in latest_labels]
    label_names = [label['Name'] for label in latest_labels]
    
    # Always add context if user is referring to image, OR if it's a travel-related query
    # that could benefit from location context
    travel_keywords = ['plan', 'trip', 'visit', 'travel', 'go to', 'see', 'explore', 'itinerary', 'budget']
    has_travel_intent = any(keyword in user_input.lower() for keyword in travel_keywords)
    has_image_reference = contains_image_reference(user_input)
    
    if has_image_reference or has_travel_intent:
        enhanced_input = f"""SYSTEM CONTEXT: The user previously uploaded an image. AWS Rekognition detected these elements: {', '.join(labels_with_confidence)}.
                                The most prominent detected elements are: {', '.join(label_names[:3])}.
                                Based on the image analysis, this appears to be related to a travel destination. When the user refers to "this place", "the image", "this location", or asks travel-related questions, they are likely referring to the location/elements shown in their uploaded image.
                                User's current question: {user_input.strip()}
                            Please respond based on both the user's question and the image context provided above."""
        return enhanced_input
    
    return user_input

def render_input_form():
    with st.form("prompt_form", clear_on_submit=True):
        user_input = st.text_area(
            "Ask me anything about your trip...",
            placeholder="e.g., Plan a 4-day trip to Paris for €2000",
            label_visibility="collapsed",
            key="human_prompt",
            height=70,
            help="Tip: Use Shift+Enter for new lines, Ctrl+Enter to send"
        )

        uploaded_img = st.file_uploader("Upload an image", type=("jpg", "jpeg", "png"), key="image_upload")

        col1, col2, col3 = st.columns([3, 1, 1])
        with col3:
            submitted = st.form_submit_button(
                "Send ➤",
                type="primary",
                on_click=on_click_callback
            )
        with col2:
            image_submitted = st.form_submit_button("Upload Image")
        
        # Handle regular text submission
        if submitted and user_input.strip():
            # Get the latest image labels if available
            latest_labels = get_latest_image_labels()
            
            # Debug: Show what labels we found
            if latest_labels:
                st.write(f"DEBUG: Found {len(latest_labels)} labels: {[label['Name'] for label in latest_labels]}")
            else:
                st.write("DEBUG: No image labels found in history")
            
            # Always enhance input with image context if available
            vague_location_phrases = ["where is this place", "where is this", "what is this place", "tell me about this place", "what’s this location", "where was this taken"]
            lower_user_input = user_input.strip().lower()

            if any(phrase in lower_user_input for phrase in vague_location_phrases):
                # Try to infer most prominent label
                top_label = latest_labels[0]['Name'] if latest_labels else "unknown place"
                enhanced_input = f"""SYSTEM CONTEXT: The user previously uploaded an image. AWS Rekognition detected the following elements: {', '.join(labels_with_confidence)}.

            The user's current message is vague but likely refers to the image context. You should infer that they are referring to **{top_label}**, and provide helpful information about its location and significance.

            User's question: {user_input.strip()}"""
            else:
                enhanced_input = image_context

            if latest_labels:
                # Create detailed context from AWS Recognition labels
                labels_with_confidence = []
                for label in latest_labels:
                    labels_with_confidence.append(f"{label['Name']} ({label['Confidence']:.1f}% confidence)")
                
                # Always include image context in messages after an image upload
                image_context = f"""SYSTEM CONTEXT: The user previously uploaded an image containing these detected elements: {', '.join(labels_with_confidence)}

                When the user refers to "the picture", "the image", "this place", or "the location in the photo", they are referring to these detected elements. You should respond based on this image analysis.

                User's question: {user_input.strip()}"""
                
                enhanced_input = image_context
                st.write(f"DEBUG: Enhanced input length: {len(enhanced_input)} characters")
            
            # Add user message to history (original message without context)
            st.session_state.history.append(Message(origin="human", message=user_input.strip()))
            
            # Set the enhanced input for the chatbot
            st.session_state.current_user_input = enhanced_input
            st.session_state.awaiting_response = True
            st.rerun()
        
        # Handle image upload
        if image_submitted and uploaded_img:
            image_bytes = uploaded_img.read()
            labels = detect_image(image_bytes)

            # Display the uploaded image immediately
            st.image(image_bytes, caption="Uploaded Image", use_container_width=True)
            st.markdown("### Detected Labels")
            for label in labels:
                st.write(f"- **{label['Name']}**: {label['Confidence']:.1f}% confidence")
            
            label_summary = ", ".join([label['Name'] for label in labels])

            # Add image message to history
            st.session_state.history.append(
                Message(
                    origin="human", 
                    message=f"[Image uploaded: {uploaded_img.name}]",
                    image_bytes=image_bytes,
                    image_labels=labels
                )
            )

            # Add assistant response
            assistant_response = f"""I can see your uploaded image! Based on AWS Recognition analysis, I detected: {label_summary}.

This looks like it could be related to Rome, Italy (especially with the Colosseum detection). Would you like me to:
- Create a trip plan for this destination?
- Provide information about visiting this location?
- Help with travel recommendations for this area?

Just let me know what you'd like to know about this place!"""

            st.session_state.history.append(
                Message(
                    origin="assistant", 
                    message=assistant_response,
                    image_labels=labels
                ) 
            )
            
            st.rerun()


def render_chat():
    chat_placeholder = st.container()
    with chat_placeholder:
        for message in st.session_state.history:
            with st.chat_message("user" if message.origin == "human" else "assistant"):
                # Display image if present
                if hasattr(message, 'image_bytes') and message.image_bytes:
                    st.image(
                        message.image_bytes, 
                        caption="Uploaded Image" if message.origin == "human" else "Analyzed Image",
                        use_container_width=True
                    )
                
                # Display message text
                if message.message:
                    st.write(message.message)
        
        if st.session_state.awaiting_response:
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                for chunk in get_chatbot_response_stream(st.session_state.current_user_input):
                    full_response += chunk
                    response_placeholder.write(full_response + "▌")
                response_placeholder.markdown(full_response)
                st.session_state.history.append(Message(origin="assistant", message=full_response))
                st.session_state.awaiting_response = False
                st.session_state.current_user_input = ""
                st.rerun()


# Remove this duplicate code block since it's now handled in render_chat()
# The original placement was causing images to display twice
# def render_input_form():
#     with st.form("prompt_form", clear_on_submit=True):
#         user_input = st.text_area(
#             "Ask me anything about your trip...",
#             placeholder="e.g., Plan a 4-day trip to Paris for €2000",
#             label_visibility="collapsed",
#             key="human_prompt",
#             height=70,
#             help="Tip: Use Shift+Enter for new lines, Ctrl+Enter to send"
#         )

#         uploaded_img = st.file_uploader("Upload an image", type=("jpg", "jpeg", "png"), key="image_upload")

#         col1, col2, col3 = st.columns([3, 1, 1])
#         with col3:
#             submitted = st.form_submit_button(
#                 "Send ➤",
#                 type="primary",
#                 on_click=on_click_callback
#             )
#         with col2:
#             image_submitted = st.form_submit_button("Upload Image")
        
#         # Handle regular text submission
#         if submitted and user_input.strip():
#             # Get the latest image labels if available
#             latest_labels = get_latest_image_labels()
            
#             # Enhance user input with image context if available
#             enhanced_input = user_input.strip()
#             if latest_labels:
#                 label_names = [label['Name'] for label in latest_labels]
#                 enhanced_input = f"{user_input.strip()}\n\n[Context: User previously uploaded an image containing: {', '.join(label_names)}]"
            
#             # Add user message to history (original message without context)
#             st.session_state.history.append(Message(origin="human", message=user_input.strip()))
            
#             # Set the enhanced input for the chatbot
#             st.session_state.current_user_input = enhanced_input
#             st.session_state.awaiting_response = True
#             st.rerun()
        
#         # Handle image upload
#         if image_submitted and uploaded_img:
#             image_bytes = uploaded_img.read()
#             labels = detect_image(image_bytes)

#             # Display the uploaded image immediately
#             st.image(image_bytes, caption="Uploaded Image", use_container_width=True)
#             st.markdown("### Detected Labels")
#             for label in labels:
#                 st.write(f"- **{label['Name']}**: {label['Confidence']:.1f}% confidence")
            
#             label_summary = ", ".join([label['Name'] for label in labels])

#             # Add image message to history (store as base64 for database persistence)
#             import base64
#             image_b64 = base64.b64encode(image_bytes).decode()
            
#             st.session_state.history.append(
#                 Message(
#                     origin="human", 
#                     message=f"[Image uploaded: {uploaded_img.name}]",
#                     image_bytes=image_bytes,
#                     image_labels=labels
#                 )
#             )

#             # Add assistant response
#             st.session_state.history.append(
#                 Message(
#                     origin="assistant", 
#                     message=f"I can see an image with: {label_summary}. Would you like me to create a trip plan based on what I see in this image?", 
#                     image_labels=labels
#                 ) 
#             )
            
#             st.rerun()




def inject_custom_css():
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
                # Display image if present
                if hasattr(message, 'image_bytes') and message.image_bytes:
                    st.image(
                        message.image_bytes, 
                        caption="Uploaded Image" if message.origin == "human" else "Analyzed Image",
                        use_container_width=True
                    )
                
                # Display message text
                if message.message:
                    st.write(message.message)
        
        if st.session_state.awaiting_response:
            with st.chat_message("assistant"):
                response_placeholder = st.empty()
                full_response = ""
                for chunk in get_chatbot_response_stream(st.session_state.current_user_input):
                    full_response += chunk
                    response_placeholder.write(full_response + "▌")
                response_placeholder.markdown(full_response)
                st.session_state.history.append(Message(origin="assistant", message=full_response))
                st.session_state.awaiting_response = False
                st.session_state.current_user_input = ""
                st.rerun()


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
    - **Conversation Memory**: Remembers your preferences
    - **Travel Expertise**: Powered by GPT-4
    """)
    st.markdown("### 💡 Try asking:")
    st.markdown("""
    - "Plan a weekend in New York for $800"
    - "I want to visit Tokyo, I love food"
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