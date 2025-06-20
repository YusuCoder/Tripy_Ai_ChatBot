from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from db.db import get_session_history
from langchain.chat_models.base import init_chat_model
from main import langfuse_handler, LANGFUSE_ENABLED
from prompts.prompt import get_flight_system_prompt
from agent.agent_utils import invoke, stream
from langchain_core.runnables.history import RunnableWithMessageHistory
import os

def get_flight_agent(session_id: str = None):
    callbacks = [langfuse_handler] if LANGFUSE_ENABLED else []
    llm = init_chat_model(
        model="openai:gpt-4o-mini",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("API_KEY"),
        temperature=0.7,
        max_tokens=2000,
        frequency_penalty=0,
        callbacks=callbacks,
    )

    fligt_agent_prompt = ChatPromptTemplate.from_messages([
            ("system", get_flight_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

    agent = create_tool_calling_agent(llm, fligt_agent_prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        verbose=False,
        max_iterations=3,
        handle_parsing_errors=True,
        callbacks=callbacks,
    )

    class StreamableAgent:
        def __init__(self, agent_executor, llm, session_id=None):
            self.agent_executor = agent_executor
            self.llm = llm
            self.session_id = session_id
            self.callbacks = callbacks
            if session_id:
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

    return StreamableAgent(agent_executor, llm, session_id)