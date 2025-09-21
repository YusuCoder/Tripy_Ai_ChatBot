import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain_core.runnables.history import RunnableWithMessageHistory
from langfuse.langchain import CallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agent.agent_utils import invoke, stream
from prompts.prompt import get_system_prompt
from tools.tools_main import tools_handler, import_weather_tool
from db.db import (
    get_session_history,
    create_new_chat_session,
    get_all_chat_sessions,
    delete_chat_session,
    get_chat_history_for_session
)

# Load environment variables from .env file
load_dotenv()
# Setting up Langfuse tracer for monitoring

langfuse_handler, LANGFUSE_ENABLED = tools_handler()

def create_weather_tool():
    return import_weather_tool()

def create_travel_planning_tool():
    """Import and create the travel planning tool"""
    try:
        from tools.travel_planning_tool_new import create_travel_planning_tool
        return create_travel_planning_tool()
    except ImportError:
        print("Warning: Could not import travel_planning_tool_new")
        return None


def get_travel_agent(session_id: str = None):
    callbacks = [langfuse_handler] if LANGFUSE_ENABLED else []
    """Get a travel agent with optional session ID for chat history"""
    
    # Get API key from environment
    api_key = os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("No API key found. Please set API_KEY or OPENAI_API_KEY in your .env file")
    
    print(f"Using API key: {api_key[:10]}..." if api_key else "No API key found")
    print(f"API key starts with: {api_key[:10] if api_key else 'None'}")
    print(f"Is OpenRouter key: {api_key.startswith('sk-or-') if api_key else False}")
    
    # Configure LLM based on API key type
    if api_key.startswith("sk-or-"):
        # OpenRouter configuration
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",  # Use a model that's available on OpenRouter
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=api_key,
            temperature=0.7,
            max_tokens=2000,
            frequency_penalty=0.5,
            callbacks=callbacks, 
        )
        print("🔗 Using OpenRouter API")
    else:
        # Direct OpenAI configuration
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=api_key,
            temperature=0.7,
            max_tokens=2000,
            frequency_penalty=0.5,
            callbacks=callbacks, 
        )
        print("🔗 Using Direct OpenAI API")

    # Create tools
    tools = [create_weather_tool()]
    
    # Add travel planning tool
    travel_tool = create_travel_planning_tool()
    if travel_tool:
        tools.append(travel_tool)

    # Create agent using the older langchain API
    agent_executor = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,  # Enable verbose for debugging
        handle_parsing_errors=True,
        max_iterations=20,  # Increased for complex travel planning workflow
        early_stopping_method="force",  # Changed to force to ensure both tools are used
        callbacks=callbacks,
        return_intermediate_steps=True,  # Enable intermediate steps capture
    )

    # For Streamlit compatibility, a simple wrapper around the agent for use in streamlit
    class StreamableAgent:
        def __init__(self, agent_executor, llm, session_id=None):
            self.agent_executor = agent_executor
            self.llm = llm
            self.session_id = session_id
            self.callbacks = callbacks

            if session_id:
                # If session_id provided, wrap with message history
                self.agent_with_history = RunnableWithMessageHistory(
                    self.agent_executor,
                    get_session_history,
                    input_message_key="input",
                    history_message_key="chat_history",
                )
            else:
                self.agent_with_history = None

        def invoke(self, messages):
            return invoke(self, messages)
        
        def stream(self, messages):
            return stream(self, messages)

    # Updated to pass session_id to StreamableAgent
    streamable_agent = StreamableAgent(agent_executor, llm, session_id)
    return streamable_agent, None  #None is for memory, because i use SqlChatMessageHistory for session history
