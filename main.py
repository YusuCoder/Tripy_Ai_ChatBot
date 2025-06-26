import os 
from dotenv import load_dotenv
from langchain.chat_models.base import init_chat_model
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.runnables.history import RunnableWithMessageHistory
from langfuse.langchain import CallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agent.agent_utils import invoke, stream
from prompts.prompt import get_system_prompt, get_flight_system_prompt
from tools.tools_main import tools_handler, import_weather_tool
from agent.langgraph_archestrator import MultiAgentOrchestrator
from db.db import (
    get_session_history,
    create_new_chat_session,
    get_all_chat_sessions,
    delete_chat_session,
    get_chat_history_for_session
)


load_dotenv(dotenv_path="./config/.env")

# Setting up Langfuse tracer for monitoring
langfuse_handler, LANGFUSE_ENABLED = tools_handler()

def create_weather_tool():
    return import_weather_tool()


def get_travel_agent(session_id: str = None):
    """Get a travel agent with optional session ID for chat history"""
    callbacks = [langfuse_handler] if LANGFUSE_ENABLED else []

    orchestratr = MultiAgentOrchestrator()

    class StreamableMultiAgent:
        def __init__(self, orchestrator, session_id=None):
            self.orchestrator = orchestrator
            self.session_id = session_id
            self.callbacks = callbacks

            if session_id:
                self.session_id = session_id
            else:
                self.session_id = None
        
        def invoke(self, messages):
            if isinstance(messages, list) and len(messages) > 0:
                user_input = ""
                chat_history = []

                for msg in messages:
                    if hasattr(msg, 'content'):
                        if msg.__class__.__name__ == 'HumanMessage':
                            user_input = msg.content
                        else:
                            chat_history.append(msg)
                
                session_history = []
                if self.session_id:
                    try:
                        session_history = get_session_history(self.session_id)
                        if hasattr(session_history, 'messages'):
                            chat_history = session_history.messages
                            # chat_history = session_history.messages + chat_history
                    except Exception as e:
                        print(f"Warning: Could not load session history: {e}")
                
                final_chat_history = chat_history

                if user_input:
                    result = self.orchestrator.run(user_input, final_chat_history)

                    if self.session_id:
                        try:
                            session_history = get_session_history(self.session_id)
                            session_history.add_user_message(user_input)
                            session_history.add_ai_message(result)
                        except Exception as e:
                            print(f"Warning: Could not save session history: {e}")
                        
                    return {"output": result}
                else:
                    return {"output": "No valid input provided."}
            else:
                # Handle string input or other formats
                input_str = str(messages) if messages else ""
                if input_str:
                    result = self.orchestrator.run(input_str, [])
                    return {"output": result}
                else:
                    return {"output": "No valid input provided."}
                

        def stream(self, messages):
            """Stream responses from the multi-agent orchestrator"""
            if isinstance(messages, list):
                user_input = ""
                chat_history = []

                for msg in messages:
                    if hasattr(msg, 'content'):
                        if msg.__class__.__name__ == 'HumanMessage':
                            user_input = msg.content
                        else:
                            chat_history.append(msg)
                
                session_history = []
                if self.session_id:
                    try:
                        session_history = get_session_history(self.session_id)
                        if hasattr(session_history, 'messages'):
                            chat_history = session_history.messages
                    except Exception as e:
                        print(f"Warning: Could not load session history: {e}")

                final_chat_history = chat_history

                if user_input:
                    """Stream responses from the orchestrator"""
                    full_response = ""
                    for chunk in self.orchestrator.stream(user_input, final_chat_history):
                        full_response += chunk
                        # Creating a chunk-like object for compatibility
                        class StreamChunk:
                            def __init__(self, content):
                                self.content = content
                        yield StreamChunk(chunk)
                    
                    # Save to session history only once here, after streaming is complete
                    if self.session_id:
                        try:
                            session_history = get_session_history(self.session_id)
                            session_history.add_user_message(user_input)
                            session_history.add_ai_message(full_response)
                        except Exception as e:
                            print(f"Warning: Could not save session history: {e}")
                else:
                    class StreamChunk:
                        def __init__(self, content):
                            self.content = content
                    yield StreamChunk("No valid input provided.")
            else:
                # Handle string input or other formats
                input_str = str(messages) if messages else ""
                if input_str:
                    for chunk in self.orchestrator.stream(input_str, []):
                        class StreamChunk:
                            def __init__(self, content):
                                self.content = content
                        yield StreamChunk(chunk)
                else:
                    class StreamChunk:
                        def __init__(self, content):
                            self.content = content
                    yield StreamChunk("No valid input provided.")

    streamable_agent = StreamableMultiAgent(orchestratr, session_id)
    return streamable_agent, None
