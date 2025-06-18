import os 
from dotenv import load_dotenv
from langchain.chat_models.base import init_chat_model
from langchain.agents import create_tool_calling_agent, AgentExecutor
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


load_dotenv(dotenv_path="./config/.env")
# Setting up Langfuse tracer for monitoring

langfuse_handler, LANGFUSE_ENABLED = tools_handler()

def create_weather_tool():
    return import_weather_tool()


def get_travel_agent(session_id: str = None):
    callbacks = [langfuse_handler] if LANGFUSE_ENABLED else []
    """Get a travel agent with optional session ID for chat history"""
    llm = init_chat_model(
        model="openai:gpt-4o-mini",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("API_KEY"),
        temperature=0.7,
        max_tokens=2000,
        frequency_penalty=0.5,
        callbacks=callbacks, 
    )

    # Weather tool creation
    tools = [create_weather_tool()]

    # Defining a chat prompt template for the agent for how the LLM should behave 
    prompt = ChatPromptTemplate.from_messages([
        ("system", get_system_prompt()),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # Constructing a tool-using agent that can dynamically call the weather tool based on input
    agent = create_tool_calling_agent(llm, tools, prompt)
    # Setting up the agent executor with the defined agent and tools, handling parsing errors, and limiting iterations
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
        max_iterations=5,
        callbacks=callbacks,
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
