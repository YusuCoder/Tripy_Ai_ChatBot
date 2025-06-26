import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.chat_models.base import init_chat_model
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from flights.flight_details import get_flight_details, extract_flight_request, sort_offers
from flights.airports import Airports

class FlightAgent:
    def __init__(self):
        self.llm = init_chat_model(
            model="openai:gpt-4o-mini",
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("API_KEY"),
            temperature=0.7,
        )
        self.airports = Airports()
        self.airports.load_airports("/Users/level_3/models/firstmodel/data/airports.dat")
        self.tools = [self.search_flights]
        # self.tools = [self.create_flight_tool()]
        self.agent = self.create_agent()


    @tool
    def search_flights(self, query: str) -> str:
        """Search for flights based on user query"""
        try:
            args = extract_flight_request(query)

            origin = self.airports.search_cities(args['origin'])
            destination = self.airports.search_cities(args['destination'])

            if not origin or not destination:
                return "No matching airports found for the provided origin or destination."
            
            origin_code = origin[0]['iata']
            destination_code = destination[0]['iata']

            offers = get_flight_details(
                origin=origin_code,
                destination=destination_code,
                departure_date=args['departure_date'],
                return_date=args.get('return_date'),
                preference=args.get('preference', 'cheapest')
            )

            if not offers:
                return "No flight offers found for the specified criteria."
            
            sorted_offers = sort_offers(offers, args.get('preference', 'cheapest'))

            response = f"✈️ Flight Search Results: {args['origin']} → {args['destination']}\n"
            response += f"📅 Departure: {args['departure_date']}"
            if args.get('return_date'):
                response += f" | Return: {args['return_date']}"
            response += f"\n🎯 Preference: {args.get('preference', 'cheapest')}\n\n"


            for i, offer in enumerate(sorted_offers[:3]):
                price = offer['price']['total']
                currency = offer['price']['currency']
                response += f"Option {i+1}: {currency} {price}\n"

                for j, itinerary in enumerate(offer['itineraries']):
                    flight_type = "Outbound" if j == 0 else "Return"
                    response += f"  {flight_type}: "

                    segments = []
                    for segment in itinerary['segments']:
                        dep_time = segment['departure']['at'].split("T")[1][:5]  # Extract time only
                        arr_time = segment['arrival']['at'].split("T")[1][:5]
                        dep_airport = segment['departure']['iataCode']
                        arr_airport = segment['arrival']['iataCode']
                        segments.append(f"{dep_airport} ({dep_time}) → {arr_airport} ({arr_time})")
                    
                    response += " | ".join(segments) + "\n"
                response += "\n"
            return response
        
        except Exception as e:
            return f"Error processing flight search: {str(e)}"
        
    def create_flight_tool(self):
        return self.search_flights
    

    def create_agent(self):
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a flight booking assistant. Your role is to:
             1. Search for flights based on user requirements.
             2. Provide detailed flight options including prices, times, and airlines.
             3. Offer alternative options when possible
             4. Help users understand flight details and make informed decisions.
             
             Always use the search_flights tool when user asks about flights, and provide clear, formal responses."""),
             MessagesPlaceholder(variable_name="chat_history"),
             ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=5,
        )
    

    def run(self, query: str, chat_history: list = None) -> str:
        """Run agent with user query and optional chat history"""
        return self.agent.invoke({
            "input": query,
            "chat_history": chat_history or []
        })["output"]
    