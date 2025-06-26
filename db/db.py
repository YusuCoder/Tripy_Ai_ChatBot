import os 
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import uuid
import sqlite3


def get_session_history(session_id: str) -> SQLChatMessageHistory:
    """Get chat message history for a specific session"""
    return SQLChatMessageHistory(session_id=session_id, connection="sqlite:///travel_chats.db")


def create_new_chat_session():
    """Create a new chat session ID"""
    return str(uuid.uuid4())


def get_all_chat_sessions():
    """Get all existing chat sessions IDs"""
    try:
        conn = sqlite3.connect("travel_chats.db")
        cursor = conn.cursor()

        cursor.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='message_store'""")

        if not cursor.fetchone():
            conn.close()
            return []

        cursor.execute("SELECT DISTINCT session_id FROM message_store ORDER BY rowid DESC")
        sessions = [row[0] for row in cursor.fetchall()]
        conn.close()
        return sessions
    except Exception as e:
        return []


def delete_chat_session(session_id: str):
    """Delete a specific chat session by ID"""
    try:
        history = get_session_history(session_id)
        history.clear()
        return True
    except Exception as e:
        print(f"Error deleting session {session_id}: {e}")
        return False


def get_chat_history_for_session(session_id: str):
    """Get chat history for a specific session"""
    try:
        history = get_session_history(session_id)
        messages = []
        for message in history.messages:
            if hasattr(message, 'content'):
                msg_type = "human" if message.__class__.__name__ == 'HumanMessage' else "assistant"
                messages.append({
                    "origin": msg_type, 
                    "content": message.content
                })
        return messages
    except Exception as e:
        print(f"Error retrieving history for session {session_id}: {e}")
        return []