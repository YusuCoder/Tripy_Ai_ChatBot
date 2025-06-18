import os 
from dotenv import load_dotenv
from langchain.chat_models.base import init_chat_model
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.runnables.history import RunnableWithMessageHistory
from langfuse.langchain import CallbackHandler
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


def tools_handler():
    """Initialize and return the tools handler"""
    load_dotenv(dotenv_path="./config/.env") 
    try:
        langfuse_secret = os.getenv("LANGFUSE_SECRET_KEY")
        langfuse_public = os.getenv("LANGFUSE_PUBLIC_KEY") 
        langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        if not langfuse_secret or not langfuse_public:
            raise ValueError("LANGFUSE_SECRET_KEY and LANGFUSE_PUBLIC_KEY must be set in environment variables")

        # Setting environment variables explicitly
        os.environ["LANGFUSE_SECRET_KEY"] = langfuse_secret
        os.environ["LANGFUSE_PUBLIC_KEY"] = langfuse_public
        os.environ["LANGFUSE_HOST"] = langfuse_host

        langfuse_handler = CallbackHandler()

        print("Langfuse handler initialized successfully.")
        print(f"   Host: {langfuse_host}")
        print(f"   Public Key: {langfuse_public[:8]}...")
        LANGFUSE_ENABLED = True

    except Exception as e:
        print(f"Failed to initialize Langfuse handler:")
        print(f"   Error: {e}")
        langfuse_handler = None
        LANGFUSE_ENABLED = False
    return langfuse_handler, LANGFUSE_ENABLED


def import_weather_tool():
    """Import the weather tool, handling import errors gracefully"""
    try:
        from tools.weather_tool import create_weather_tool
        return create_weather_tool()
    except ImportError:
        print("Warning: Could not import weather_tool. Creating dummy tool.")
        def create_weather_tool():
            """Dummy weather tool if import fails"""
            from langchain.tools import tool

            @tool
            def get_weather(location: str) -> str:
                """Get weather for a location (dummy implementation)"""
                return f"Weather tool not available. Please check your tools/weather_tool.py file."

            return get_weather