import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.chat_models.base import init_chat_model
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from tools.weather_tool import create_weather_tool
import datetime


load_dotenv(dotenv_path="./config/.env")
today = datetime.date.today().strftime("%B %d, %Y")

def get_travel_agent():
    llm = init_chat_model(
        model="openai:gpt-4o-mini",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("API_KEY"),
        temperature=0.7,
        max_tokens=1000,
        frequency_penalty=0.5,
    )
    
    memory = ConversationBufferMemory(
        k=3,
        return_messages=True,
    )

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

    # For Streamlit compatibility, a simple wrapper arount the agent for use in streamlit
    class StreamableAgent:
        def __init__(self, agent_executor, llm):
            self.agent_executor = agent_executor
            self.llm = llm
            
        # This takes a list of LangChain messages (like SystemMessage, HumanMessage, AIMessage).
        # Extracts the latest human message as input.
        # Collects the rest of the messages as chat history (excluding system ones).
        # Calls the LangChain agent executor
        def invoke(self, messages):
            # Handling both message format and direct input
            if isinstance(messages, list):
                # Extracting the last user message
                user_input = ""
                chat_history = []
                for msg in messages:
                    if hasattr(msg, 'content'):
                        if msg.__class__.__name__ == 'HumanMessage':
                            user_input = msg.content
                        elif msg.__class__.__name__ == 'SystemMessage':
                            continue                                     # Skiping system messages for history
                        else:
                            chat_history.append(msg)
                
                return self.agent_executor.invoke({
                    "input": user_input,
                    "chat_history": chat_history
                })
            else:
                return self.agent_executor.invoke(messages)
        
        def stream(self, messages):
            # For streaming, i use the LLM directly with a simplified approach
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

    streamable_agent = StreamableAgent(agent_executor, llm)
    return streamable_agent, memory


# This function defines the core personality and logic of the travel agent.
# It instructs the agent to: 
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
        f"And remember todays date is {today}".

        When helping a user plan trips:
        1. Ask clarifying questions about destination, budget, dates, and preferences.
        2. Use the get_weather tool to check the weather for the destination and dates.
        3. After retrieving the weather, proceed to provide a structured, day-by-day itinerary, including practical tips, local insights, estimated costs, and time for activities.
        4. Be enthusiastic and helpful.

        Always format your itineraries clearly with days, items, activities, and brief descriptions.
        Do not stop after providing the weather—ALWAYS continue and provide the full itinerary unless the user says to stop.
    """


def main():
    print("Welcome to the Smart Trip Planner!")
    print("=" * 40)
    print("Hi! I'm Tripy, your personal travel planning assistant.")
    print("Tell me where you'd like to go and I'll help you plan the perfect trip!")
    print("Type 'quit' to exit at any time.\n")

    streamable_agent, memory = get_travel_agent()
    
    while True:
        user_input = input(">>> : ").strip()

        if user_input.lower() == "quit":
            print("Goodbye!")
            break
        if not user_input:
            continue
    
        try:
            # Get conversation history
            history = memory.chat_memory.messages
            
            # Invoke the agent executor with the input and chat history
            response = streamable_agent.agent_executor.invoke({
                "input": user_input,
                "chat_history": history
            })

            # Extract the output from the response
            output = response.get("output", "")
            print(f"Tripy: {output}\n")

            # Save the conversation to memory
            memory.save_context(
                {"input": user_input},
                {"output": output}
            )
        except Exception as e:
            print(f"Sorry, I encountered an error: {e}")
            print("Please try again!\n")


if __name__ == "__main__":
    main()
