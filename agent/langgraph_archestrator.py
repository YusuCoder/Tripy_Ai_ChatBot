import operator
import os
import time
from typing import Any, Dict, List, Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain.chat_models.base import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from agent.flight_agent import FlightAgent
from tools.tools_main import import_weather_tool
from prompts.prompt import get_system_prompt
import datetime

today = datetime.date.today().strftime("%B %d, %Y")
class AgentState(TypedDict):
    """State of the agent with memory and chat history."""
    messages: Annotated[List[BaseMessage], operator.add]
    user_input: str
    current_agent: str
    flight_results: str
    weather_results: str
    final_response: str


class MultiAgentOrchestrator:

    def __init__(self):
        self.llm = init_chat_model(
            model="openai:gpt-4o-mini",
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("API_KEY"),
            temperature=0.7,
        )

        self.flight_agent = FlightAgent()
        self.weather_tool = import_weather_tool()


        self.graph = self.create_graph()

    def create_router_agent(self):
        router_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a smart router that determines which specialis agent should handle user's request.
             Available agents are:
             - flight_agent: Handles flight searches, flight information, airline details
             - travel_agent: handles general travel planning, recommendations, itineraries, accommodations, and activities
             - weather_agent: Provides weather forecast and handles weather-related informations
             
             Analyze the user's input and determine wich agent(s) should hande it.
             
             Response format:
             - If it's about flights, "flight_agent"
             - If it's about weather, "weather_agent"
             - If it's about general travel planning: "travel_agent"
             - If it needs multiple agents: "travel_agent" (travel agent can coordinate with others)
             
             Only respond with the agent namem nothing else."""      
             ), ("human", "{input}"),])
        
        return router_prompt | self.llm
    

    def route_request(self, state: AgentState) -> str:
        """Route the request to the appropriate agent"""
        user_input = state["user_input"].lower()

        # More comprehensive flight keywords detection
        flight_keywords = [
            'flight', 'flights', 'fly', 'flying', 'airline', 'airlines', 
            'airport', 'airports', 'departure', 'arrival', 'depart', 'arrive',
            'rome to', 'from rome', 'to stuttgart', 'from stuttgart',
            'ticket', 'tickets', 'book', 'booking', 'travel from', 'travel to',
            'round trip', 'return flight', 'one way'
        ]

        # Check for flight-related patterns
        flight_patterns = [
            'from ' in user_input and 'to ' in user_input,  # "from X to Y" pattern
            any(keyword in user_input for keyword in flight_keywords),
            'departure' in user_input or 'return' in user_input,
            any(month in user_input for month in ['january', 'february', 'march', 'april', 'may', 'june', 
                                                 'july', 'august', 'september', 'october', 'november', 'december']),
            any(date_pattern in user_input for date_pattern in ['st ', 'nd ', 'rd ', 'th ', '/']),
        ]

        if any(flight_patterns):
            print(f"Routing to flight_agent for query: {user_input}")
            return "flight_agent"

        # Weather keywords detection
        weather_keywords = ['weather', 'forecast', 'temperature', 'rain', 'sunny', 'cloudy', 'snow']
        if any(keyword in user_input for keyword in weather_keywords):
            print(f"Routing to weather_agent for query: {user_input}")
            return "weather_agent"

        # Travel keywords detection
        travel_keywords = ['itinerary', 'plan', 'trip', 'visit', 'go to', 'travel to', 'vacation', 'holiday']
        if any(keyword in user_input for keyword in travel_keywords):
            print(f"Routing to travel_agent for query: {user_input}")
            return "travel_agent"

        # Default to travel_agent
        print(f"Defaulting to travel_agent for query: {user_input}")
        return "travel_agent"

        
     
    def flight_agent_node(self, state: AgentState) -> AgentState:
        """Handle agent processing node"""
        print("Processing flight agent node...")

        try:
            chat_history = []
            for msg in state.get("messages", []):
                if isinstance(msg, (HumanMessage, AIMessage)) and msg.content != state["user_input"]:
                    chat_history.append(msg)

            flight_response = self.flight_agent.run(state["user_input"], chat_history)

            state["flight_results"] = flight_response
            state["current_agent"] = "flight_agent"
        except Exception as e:
            error_msg = (f"❌ Error in flight agent processing: {e}")
            state["flight_results"] = error_msg
        
        return state
    

    def weather_agent_node(self, state: AgentState) -> AgentState:
        """Handle weather agent processing node"""
        print("Processing weather agent node...")

        try:
            weather_response = ""
            if hasattr(self.weather_tool, 'run'):
                print("Using weather_tool.run()")
                weather_response = self.weather_tool.run(state["user_input"])
            elif callable(self.weather_tool):
                print("Calling weather_tool directly")
                weather_response = self.weather_tool(state["user_input"])
            else:
                print("Using weather_tool.invoke()")
                weather_response = self.weather_tool.invoke({"query": state["user_input"]})

            print(f"Weather response: {weather_response[:200]}...")
            state["weather_results"] = weather_response
            state["current_agent"] = "weather_agent"
        except Exception as e:
            error_msg = f"❌ Error in weather agent processing: {e}"
            print(error_msg)
            state["weather_results"] = error_msg
        return state
    

    def travel_agent_node(self, state: AgentState) -> AgentState:
        """Handle travel agent processing node"""
        print("Processing travel agent node...")

        try:
            flight_info = state.get("flight_results", "")
            weather_info = state.get("weather_results", "")

            system_prompt = """Y

            Your expertise includes:
            - Creating detailed day-by-day itineraries
            - Budget planning and cost estimation
            - Recommending activities, restaurants, and accommodations
            - Adapting to different travel styles (e.g., adventure, relaxation, cultural immersion, etc.)
            - Using current weather and forecasts to suggest appropriate activities
            - Considering travel logistics and timing
            - While choosing the restaurants ask user about their preferences (e.g., vegetarian, vegan, local cuisine, etc.)

            Available informations:

            IMPORTANT: When planning trips, always check the weather for the destination to provide weather-appropriate recommendations. 
            Use the most accurate weather informations to give exact advice when users mention a destination and if there is no exact date provided in the prompt calculate a date from the current day.
            And remember today's date is {today}.

            IMPORTANT: When helping a user plan trips:
            1. Always ask clarifying questions about destination, budget, dates, and preferences, and questions should be bullet pointed.
            2. Use the get_weather tool to check the weather for the destination and dates.
            3. After retrieving the weather, proceed to provide a structured, day-by-day itinerary, including practical tips, local insights, estimated costs, and time for activities.
            4. Be enthusiastic and helpful.

            IMPORTANT: When you are planning and checking the weather never stop prompting untill you create a full travel plan with all the necessasry details.
            Always format your itineraries clearly with days, items, activities, and brief descriptions.
            Do not stop after providing the weather—ALWAYS continue and provide the full itinerary unless the user says to stop.
         """ 

            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ])

            input_dict = {
                "input": state["user_input"],
                "chat_history": state.get("messages", []),
                "flight_info": flight_info,
                "weather_info": weather_info,
                "today": today
            }

            # Create and invoke the chain
            chain = prompt | self.llm
            response = chain.invoke(input_dict)

            state["final_response"] = response.content
            state["current_agent"] = "travel_agent"
        except Exception as e:
            error_msg = f"❌ Error in travel agent processing: {e}"
            print(error_msg)
            state["final_response"] = "I apologize, I'm having trouble creating your itinerary. Please try again with more specific details."

        return state

    def create_graph(self) -> StateGraph:
        """Create the state graph for the multi-agent orchestrator"""
        workflow = StateGraph(AgentState)
    
        # Add nodes
        workflow.add_node("flight_agent", self.flight_agent_node)
        workflow.add_node("weather_agent", self.weather_agent_node)
        workflow.add_node("travel_agent", self.travel_agent_node)
    
        workflow.add_conditional_edges(
            START,
            self.route_request,
            {
                "flight_agent": "flight_agent",
                "weather_agent": "weather_agent",
                "travel_agent": "travel_agent"
            }
        )
    
        workflow.add_edge("flight_agent", "travel_agent")
        workflow.add_edge("weather_agent", "travel_agent")
        workflow.add_edge("travel_agent", END)
    
        return workflow.compile()

    
    def run(self, user_input: str, chat_history: List[BaseMessage] = None):
        """Run the multi-agent system"""
        print(f"Running multi-agent orchestrator with input: {user_input[:50]}...")

        initial_state = {
            "messages": chat_history or [],
            "user_input": user_input,
            "current_agent": "",
            "flight_results": "",
            "weather_results": "",
            "final_response": ""
        }

        try:
            result = self.graph.invoke(initial_state)

            if result["current_agent"] == "flight_agent":
                return result["flight_results"]
            elif result["current_agent"] == "weather_agent":
                return result["weather_results"]
            elif result["current_agent"] == "travel_agent":
                return result["final_response"]
            else:
                return "I apologize, I'm having trouble processing your request. Please try again later."
        except Exception as e:
            print(f"❌ Error in multi-agent orchestrator run: {e}")
            return f"I encountered an error while processing your request: {e}"
        
    
    def stream(self, user_input: str, chat_history: List[BaseMessage] = None):
        """Stream the response from the multi-agent system"""
        print(f"Streaming response for input: {user_input[:50]}...")
    
        initial_state = {
            "messages": chat_history or [],
            "user_input": user_input,
            "current_agent": "",
            "flight_results": "",
            "weather_results": "",
            "final_response": ""
        }
    
        try:
            # Use graph.stream() directly
            # This will yield dictionaries representing events
            for s in self.graph.stream(initial_state):
                for key, value in s.items():
                    if key == "travel_agent": # Or whatever agent is currently processing
                        # Extract the final_response or messages from the state
                        if "final_response" in value:
                            for char in value["final_response"]: # Simulating char by char
                                yield char
                                time.sleep(0.01)
                    # You might also want to stream intermediate thoughts or tool calls
                    # For example, if 'messages' field is being updated:
                    if key == 'messages':
                        # Look for new AIMessages or partial content
                        for msg in value:
                            if isinstance(msg, AIMessage) and hasattr(msg, 'content'):
                                # This is simplistic, a full stream handler would differentiate new tokens
                                for char in msg.content: # Yield new content token by token
                                    yield char
                                    time.sleep(0.01)
                # You'll need a more robust way to capture the final conversational output
                # from the stream. This often involves accumulating tokens.
    
        except Exception as e:
            error_msg = f"❌ Error in streaming response: {e}"
            for char in error_msg:
                yield char
                time.sleep(0.01)
