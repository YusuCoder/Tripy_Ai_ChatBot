### SMART TRIP PLANNER\
import os 
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.chat_models.base import init_chat_model


load_dotenv(dotenv_path="./config/.env")

def get_travel_agent():

    llm = init_chat_model(
        model="openai:gpt-4.1-nano",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("API_KEY"),
        temperature=0.7,
        max_tokens=200,
    )
    

    memory = ConversationBufferMemory(
        k=3,
        return_messages=True,
    )

    return llm, memory


def get_system_prompt():
    return """You are a travel agent specializing in creating personalized trip itineraries.

    Your expertise includes:
    - Creating detailed day-by-day itineraries
    - Budget planning and cost estimation
    - Recommending activities, restaurants, and accommodations
    - Adapting to different travel styles (e.g.., advanture, rexaxation, cultural immersion, etc.)

    When helping a user plan trips:
    1. Ask clarifying questions about destination, budget, dates, and precferences.
    2. Provide structured, day-by-day itineraries
    3. Give practical tips and local insights.
    4. Include estimated costs and time for activitiesm
    5. Be enthusiastic and helpful.

    
    Alwayts format your itineraries clearly with days, items, activities, and brief descriptions."""


def main():

    print("Welcome to the Smart Trip Planner!")
    print("=" * 40)
    print("Hi! I'm Tripy, your personal travel planning assistant.")
    print("Tell me where you'd like to go and I'll help you plan the perfect trip!")
    print("Type 'quit' to exit at any tyme.\n")


    agent, memory = get_travel_agent()
    system_prompt = get_system_prompt()

    
    while True:
        user_input = input(">>> : ").strip()

        if (user_input.lower() == "quit"):
            print("GoodBye!")
            break
        if not user_input:
            continue
    
        try:
            history = memory.chat_memory.messages
            messages = [SystemMessage(content=system_prompt)]
            messages.extend(history)
            messages.append(HumanMessage(content=user_input))

            response = agent.invoke(messages)

            print(f"Tripy: {response.content}\n")

            memory.save_context(
                {"input": user_input},
                {"output": response.content}
            )
        except Exception as e:
            print(f"Sorry, I encountered an error: {e}")
            print("Please try again!\n")


if __name__ == "__main__":
    main()

