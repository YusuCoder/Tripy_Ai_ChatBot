import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models.base import init_chat_model
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
import datetime

# Updated import for SQLChatMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import uuid

# Import weather tool (make sure this doesn't cause circular imports)
try:
    from tools.weather_tool import create_weather_tool
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

load_dotenv(dotenv_path="./config/.env")
today = datetime.date.today().strftime("%B %d, %Y")

def get_session_history(session_id: str) -> SQLChatMessageHistory:
    """Get chat message history for a specific session"""
    return SQLChatMessageHistory(session_id=session_id, connection="sqlite:///travel_chats.db")


def get_travel_agent(session_id: str = None):
    llm = init_chat_model(
        model="openai:gpt-4o-mini",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("API_KEY"),
        temperature=0.7,
        max_tokens=2000,
        frequency_penalty=0.5,
    )

    # Weather tool creation
    tools = [create_weather_tool()]

    # Defining a chat prompt template for the agent for how the LLM should behave 
    prompt = ChatPromptTemplate.from_messages([
        ("system", get_system_prompt()),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
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
    )

    # For Streamlit compatibility, a simple wrapper around the agent for use in streamlit
    class StreamableAgent:
        def __init__(self, agent_executor, llm, session_id=None):
            self.agent_executor = agent_executor
            self.llm = llm
            self.session_id = session_id  # Fixed typo: was session_iud

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

        # def invoke(self, messages):
        #     if hasattr(self, 'session_id') and self.session_id and self.agent_with_history:
        #         # Handling both message format and direct input
        #         # Extracting the last user message
        #         user_input = ""
        #         if isinstance(messages, list) and len(messages) > 0:
        #             for msg in messages:
        #                 if hasattr(msg, 'content') and msg.__class__.__name__ == 'HumanMessage':
        #                     user_input = msg.content
        #                     break
        #         elif isinstance(messages, str):
        #             user_input = messages
        #         else:
        #             user_input = str(messages)
                
        #         if user_input:
        #             return self.agent_with_history.invoke(
        #                 {"input": user_input},
        #                 config={"configurable": {"session_id": self.session_id}},
        #             )
        #         else:
        #             return {"output": "No valid input provided."}
        #     else:
        #         # If no session_id is provided, using original existing buffer memory
        #         if isinstance(messages, list) and len(messages) > 0:
        #             user_input = ""
        #             chat_history = []
        #             for msg in messages:
        #                 if hasattr(msg, 'content'):
        #                     if msg.__class__.__name__ == 'HumanMessage':
        #                         user_input = msg.content
        #                     elif msg.__class__.__name__ == 'SystemMessage':
        #                         continue
        #                     else:
        #                         chat_history.append(msg)
                    
        #             if user_input:
        #                 return self.agent_executor.invoke({
        #                     "input": user_input,
        #                     "chat_history": chat_history
        #                 })
        #             else:
        #                 return {"output": "No valid input provided."}
        #         else:
        #             # Handle string input or other formats
        #             input_str = str(messages) if messages else ""
        #             if input_str:
        #                 return self.agent_executor.invoke({"input": input_str})
        #             else:
        #                 return {"output": "No valid input provided."}
        def invoke(self, messages):
            if self.session_id and self.agent_with_history:
                # Handling both message format and direct input
                # Extracting the last user message
                user_input = ""
                if isinstance(messages, list) and len(messages) > 0:
                    for msg in messages:
                        if hasattr(msg, 'content') and msg.__class__.__name__ == 'HumanMessage':
                            user_input = msg.content
                            break
                elif isinstance(messages, str):
                    user_input = messages
                else:
                    user_input = str(messages)
                
                if user_input:
                    return self.agent_with_history.invoke(
                        {"input": user_input},
                        config={"configurable": {"session_id": self.session_id}},
                    )
                else:
                    return {"output": "No valid input provided."}
            else:
                # If no session_id is provided, using original existing buffer memory
                if isinstance(messages, list) and len(messages) > 0:
                    user_input = ""
                    chat_history = []
                    for msg in messages:
                        if hasattr(msg, 'content'):
                            if msg.__class__.__name__ == 'HumanMessage':
                                user_input = msg.content
                            elif msg.__class__.__name__ == 'SystemMessage':
                                continue
                            else:
                                chat_history.append(msg)
                    
                    if user_input:
                        return self.agent_executor.invoke({
                            "input": user_input,
                            "chat_history": chat_history
                        })
                    else:
                        return {"output": "No valid input provided."}
                else:
                    # Handle string input or other formats
                    input_str = str(messages) if messages else ""
                    if input_str:
                        return self.agent_executor.invoke({"input": input_str})
                    else:
                        return {"output": "No valid input provided."}
                    
        def stream(self, messages):
            # For streaming, use the LLM directly with a simplified approach
            if isinstance(messages, list):
                # Convert messages to a single prompt
                prompt_parts = []
                for msg in messages:
                    if hasattr(msg, 'content'):
                        if msg.__class__.__name__ == 'SystemMessage':
                            prompt_parts.append(f"System: {msg.content}")
                        elif msg.__class__.__name__ == 'HumanMessage':
                            prompt_parts.append(f"Human: {msg.content}")
                        elif msg.__class__.__name__ == 'AIMessage':
                            prompt_parts.append(f"Assistant: {msg.content}")
                
                full_prompt = "\n\n".join(prompt_parts)
                full_prompt += "\n\nAssistant: "
                
                # Stream the response
                for chunk in self.llm.stream(full_prompt):
                    if hasattr(chunk, 'content') and chunk.content:
                        yield chunk
            else:
                # Fallback for non-list input
                for chunk in self.llm.stream(str(messages)):
                    if hasattr(chunk, 'content') and chunk.content:
                        yield chunk

    # Updated to pass session_id to StreamableAgent
    streamable_agent = StreamableAgent(agent_executor, llm, session_id)
    return streamable_agent, None  # Return None for memory since we're using SQLChatMessageHistory


# Creating a new chat session
def create_new_chat_session():
    """Create a new chat session ID"""
    return str(uuid.uuid4())

def get_all_chat_sessions():
    """Get all existing chat sessions IDs"""
    import sqlite3
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
                    "origin": msg_type,  # Changed from "type" to "origin" to match streamlit_app.py
                    "content": message.content
                })
        return messages
    except Exception as e:
        print(f"Error retrieving history for session {session_id}: {e}")
        return []


def get_system_prompt():
    return f"""
        You are a travel agent specializing in creating personalized trip itineraries.

        Your expertise includes:
        - Creating detailed day-by-day itineraries
        - Budget planning and cost estimation
        - Recommending activities, restaurants, and accommodations
        - Adapting to different travel styles (e.g., adventure, relaxation, cultural immersion, etc.)
        - Using current weather and forecasts to suggest appropriate activities
        - Considering travel logistics and timing
        - While choosing the restaurants ask user about their preferences (e.g., vegetarian, vegan, local cuisine, etc.)

        IMPORTANT: When planning trips, always check the weather for the destination to provide weather-appropriate recommendations. 
        Use the most accurate weather informations to give exact advice when users mention a destination and if there is no exact date provided calculate a date from the current day.
        And remember today's date is {today}.

        When helping a user plan trips:
        1. Ask clarifying questions about destination, budget, dates, and preferences.
        2. Use the get_weather tool to check the weather for the destination and dates.
        3. After retrieving the weather, proceed to provide a structured, day-by-day itinerary, including practical tips, local insights, estimated costs, and time for activities.
        4. Be enthusiastic and helpful.

        Always format your itineraries clearly with days, items, activities, and brief descriptions.
        Do not stop after providing the weather—ALWAYS continue and provide the full itinerary unless the user says to stop.
    """


# import os 
# from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
# from langchain_core.messages import HumanMessage, SystemMessage
# from langchain_core.prompts import PromptTemplate
# from langchain.chains import LLMChain
# from langchain.memory import ConversationBufferMemory
# from langchain.chat_models.base import init_chat_model
# from langchain.agents import create_tool_calling_agent, AgentExecutor
# from langchain_core.prompts import ChatPromptTemplate
# from tools.weather_tool import create_weather_tool
# import datetime

# from langchain_community.chat_message_histories import SQLChatMessageHistory
# from langchain_core.runnables.history import RunnableWithMessageHistory
# import uuid

# load_dotenv(dotenv_path="./config/.env")
# today = datetime.date.today().strftime("%B %d, %Y")

# def get_session_history(session_id: str) -> SQLChatMessageHistory:
#     """Get chat message history for a specific session"""
#     return SQLChatMessageHistory(session_id=session_id, connection="sqlite:///travel_chats.db")


# def get_travel_agent(session_id: str = None):
#     llm = init_chat_model(
#         model="openai:gpt-4o-mini",
#         base_url="https://openrouter.ai/api/v1",
#         api_key=os.getenv("API_KEY"),
#         temperature=0.7,
#         max_tokens=2000,
#         frequency_penalty=0.5,
#     )

#     if session_id:
#         # Using SQLite-backend memory for presistance
#         memory = SQLChatMessageHistory(session_id=session_id, connection="sqlite:///travel_chats.db")
#     else:
#         # Useing original buffer memory for backwards compatibility
#         memory = ConversationBufferMemory(k = 10, return_messages=True)

#     #Weather tool creation
#     tools = [create_weather_tool()]

#     # Defining a chat prompt template for the agent for how the LLM should behave 
#     prompt = ChatPromptTemplate.from_messages([
#         ("system", get_system_prompt()),
#         ("placeholder", "{chat_history}"),
#         ("human", "{input}"),
#         ("placeholder", "{agent_scratchpad}"),
#     ])

#     # Constructing a tool-using agent that can dynamically call the weather tool based on input
#     agent = create_tool_calling_agent(llm, tools, prompt)
    
#     # Setting up the agent executor with the defined agent and tools, handling parsing errors, and limiting iterations
#     agent_executor = AgentExecutor(
#         agent=agent,
#         tools=tools,
#         verbose=False,
#         handle_parsing_errors=True,
#         max_iterations=5,
#     )

#     # For Streamlit compatibility, a simple wrapper arount the agent for use in streamlit
#     class StreamableAgent:
#         def __init__(self, agent_executor, llm, session_id=None):
#             self.agent_executor = agent_executor
#             self.llm = llm
#             self.session_iud = session_id

#             if session_id:
#                 #if session_id provided, wrap with message history
#                 self.agent_with_history = RunnableWithMessageHistory(
#                     self.agent_executor,
#                     get_session_history,
#                     input_message_key="input",
#                     history_message_key="chat_history",
#                 )
#             else:
#                 self.agent_with_history = None

#         # This takes a list of LangChain messages (like SystemMessage, HumanMessage, AIMessage).
#         # Extracts the latest human message as input.
#         # Collects the rest of the messages as chat history (excluding system ones).
#         # Calls the LangChain agent executor
#         def invoke(self, messages):
#             if self.session_id and self.agent_with_history:
#             # Handling both message format and direct input
#                 # Extracting the last user message
#                 user_input = ""
#                 if isinstance(messages, list):
#                     # chat_history = []
#                     for msg in messages:
#                         if hasattr(msg, 'content') and msg.__class__.__name__ == 'HumanMessage':
#                             user_input = msg.content
#                             break
#                 else:
#                     user_input = str(messages)
                
#                 return self.agent_executor.invoke({
#                         "input": user_input},
#                         config={"configurable": {"session_id": self.session_id}},
#                     )
#             else:
#                 # If no sessuion_id is provided, using original existing buffer memory
#                 if isinstance(messages, list):
#                     user_input = ""
#                     chat_history = []
#                     for msg in messages:
#                         if hasattr(msg, 'content'):
#                             if msg.__class__.__name__ == 'HumanMessage':
#                                 user_input = msg.content
#                             elif msg.__class__.__name__ == 'SystemMessage':
#                                 continue
#                             else:
#                                 chat_history.append(msg)
                    
#                     return self.agent_executor.invoke({
#                         "input": user_input,
#                         "chat_history": chat_history
#                     })
#                 else:
#                     return self.agent_executor.invoke(messages)
        
#         def stream(self, messages):
#             # For streaming, i use the LLM directly with a simplified approach
#             if isinstance(messages, list):
#                 # Convert messages to a single prompt
#                 prompt_parts = []
#                 for msg in messages:
#                     if hasattr(msg, 'content'):
#                         if msg.__class__.__name__ == 'SystemMessage':
#                             prompt_parts.append(f"System: {msg.content}")
#                         elif msg.__class__.__name__ == 'HumanMessage':
#                             prompt_parts.append(f"Human: {msg.content}")
#                         elif msg.__class__.__name__ == 'AIMessage':
#                             prompt_parts.append(f"Assistant: {msg.content}")
                
#                 full_prompt = "\n\n".join(prompt_parts)
#                 full_prompt += "\n\nAssistant: "
                
#                 # Stream the response
#                 for chunk in self.llm.stream(full_prompt):
#                     if hasattr(chunk, 'content') and chunk.content:
#                         yield chunk
#             else:
#                 # Fallback for non-list input
#                 for chunk in self.llm.stream(str(messages)):
#                     if hasattr(chunk, 'content') and chunk.content:
#                         yield chunk

#     streamable_agent = StreamableAgent(agent_executor, llm)
#     return streamable_agent, memory

# #Creating a new chat session
# def create_new_chat_session():
#     """Create a new chat session ID"""
#     return str(uuid.uuid4())

# def get_all_chat_sessions():
#     """Get all existing chat sessions IDs"""
#     import sqlite3
#     try:
#         conn = sqlite3.connect("travel_chats.db")
#         cursor = conn.cursor()

#         cursor.execute("""SELECT name FROM sqlite_master WHERE type='table' AND name='message_store'""")

#         if not cursor.fetchone():
#             conn.close()
#             return []

#         cursor.execute("SELECT DISTINCT session_id FROM message_store ORDER BY rowid DESC")
#         sessions = [row[0] for row in cursor.fetchall()]
#         conn.close()
#         return sessions
#     except Exception as e:
#         return []

# def delete_chat_session(session_id: str):
#     """Delete a specific chat session by ID"""
#     try:
#         history = get_session_history(session_id)
#         history.clear()
#         return True
#     except Exception as e:
#         print(f"Error deleting session {session_id}: {e}")
#         return False

# def get_chat_history_for_session(session_id: str):
#     """Get chat history for a specific session"""
#     try:
#         history = get_session_history(session_id)
#         messages = []
#         for message in history.messages:
#             if hasattr(message, 'content'):
#                 msg_type = "human" if message.__class__.__name__ == 'HumanMessage' else "assistant"
#                 messages.append({
#                     "type": msg_type,
#                     "content": message.content
#                 })
#         return messages
#     except Exception as e:
#         print(f"Error retrieving history for session {session_id}: {e}")
#         return []


# # This function defines the core personality and logic of the travel agent.
# # It instructs the agent to: 
# def get_system_prompt():
#     return f"""
#         You are a travel agent specializing in creating personalized trip itineraries.

#         Your expertise includes:
#         - Creating detailed day-by-day itineraries
#         - Budget planning and cost estimation
#         - Recommending activities, restaurants, and accommodations
#         - Adapting to different travel styles (e.g., adventure, relaxation, cultural immersion, etc.)
#         - Using current weather and forecasts to suggest appropriate activities
#         - Considering travel logistics and timing
#         - While choosing the restaurants ask user about their preferences (e.g., vegetarian, vegan, local cuisine, etc.)

#         IMPORTANT: When planning trips, always check the weather for the destination to provide weather-appropriate recommendations. 
#         Use the most accurate weather informations to give exact advice when users mention a destination and if there is no exact date provided calculate a date from the current day.
#         f"And remember todays date is {today}".

#         When helping a user plan trips:
#         1. Ask clarifying questions about destination, budget, dates, and preferences.
#         2. Use the get_weather tool to check the weather for the destination and dates.
#         3. After retrieving the weather, proceed to provide a structured, day-by-day itinerary, including practical tips, local insights, estimated costs, and time for activities.
#         4. Be enthusiastic and helpful.

#         Always format your itineraries clearly with days, items, activities, and brief descriptions.
#         Do not stop after providing the weather—ALWAYS continue and provide the full itinerary unless the user says to stop.
#     """


# # def main():
# #     print("Welcome to the Smart Trip Planner!")
# #     print("=" * 40)
# #     print("Hi! I'm Tripy, your personal travel planning assistant.")
# #     print("Tell me where you'd like to go and I'll help you plan the perfect trip!")
# #     print("Type 'quit' to exit at any time.\n")

# #     streamable_agent, memory = get_travel_agent()
    
# #     while True:
# #         user_input = input(">>> : ").strip()

# #         if user_input.lower() == "quit":
# #             print("Goodbye!")
# #             break
# #         if not user_input:
# #             continue
    
# #         try:
# #             # Get conversation history
# #             history = memory.chat_memory.messages
            
# #             # Invoke the agent executor with the input and chat history
# #             response = streamable_agent.agent_executor.invoke({
# #                 "input": user_input,
# #                 "chat_history": history
# #             })

# #             # Extract the output from the response
# #             output = response.get("output", "")
# #             print(f"Tripy: {output}\n")

# #             # Save the conversation to memory
# #             memory.save_context(
# #                 {"input": user_input},
# #                 {"output": output}
# #             )
# #         except Exception as e:
# #             print(f"Sorry, I encountered an error: {e}")
# #             print("Please try again!\n")


# # if __name__ == "__main__":
# #     main()
