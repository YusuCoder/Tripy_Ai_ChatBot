import os
import json
from typing import Optional
from openai import OpenAI
from amadeus import Client, ResponseError, Location
from dotenv import load_dotenv
from datetime import datetime
from airports import Airports
load_dotenv(dotenv_path="../config/.env")
# ----------------------------
# 1. Schema for GPT function
# ----------------------------
function_schema = {
    "name": "extract_flight_request",
    "description": "Extracts flight search details from user's natural language query",
    "parameters": {
        "type": "object",
        "properties": {
            "origin": {
                "type": "string",
                "description": "Departure city and Country (e.g. Stuttgart, Germany or STR)"
            },
            "destination": {
                "type": "string",
                "description": "Arrival city and Country (e.g. Rome, Italy or FCO)"
            },
            "departure_date": {
                "type": "string",
                "description": "Departure date in YYYY-MM-DD"
            },
            "return_date": {
                "type": "string",
                "description": "Return date in YYYY-MM-DD",
                "nullable": True
            },
            "preference": {
                "type": "string",
                "enum": ["cheapest", "shortest", "direct"],
                "description": "Flight preference"
            }
        },
        "required": ["origin", "destination", "departure_date"]
    }
}
# ----------------------------------------
# 2. VALIDATE DATE FUNCTION
# ----------------------------------------
def validate_date(date_str: str) -> str:
    """Ensures the date is in the current/future year. Returns YYYY-MM-DD."""
    if not date_str:
        return date_str
    
    current_year = datetime.now().year
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    
    if date_obj.year < current_year:
        # Replace the year with the current year
        corrected_date = date_obj.replace(year=current_year)
        return corrected_date.strftime("%Y-%m-%d")
    return date_str

# ----------------------------------------
# 2. GPT function call via OpenRouter API
# ----------------------------------------
def extract_flight_request(user_input):
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("API_KEY")
    )

    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{"role": "user", "content": user_input}],
        tools=[{"type": "function", "function": function_schema}],
        tool_choice={"type": "function", "function": {"name": "extract_flight_request"}},
    )

    tool_args = response.choices[0].message.tool_calls[0].function.arguments
    args = json.loads(tool_args)

    args["departure_date"] = validate_date(args["departure_date"])
    if args.get("return_date"):
        args["return_date"] = validate_date(args["return_date"])

    return args


# --------------------------------------
# 4. Fetch flight details from Amadeus
# --------------------------------------
def get_flight_details(origin: str, destination: str, departure_date: str,
                      return_date: Optional[str] = None, preference: str = "cheapest"):
    """Fetches flight offers using Amadeus API"""
    amadeus = Client(
        client_id=os.getenv("AMADEUS_API_KEY"),
        client_secret=os.getenv("AMADEUS_API_SECRET")
    )
    try:
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": 1,
            "max": 5,
        }
        if return_date:
            params["returnDate"] = return_date
        response = amadeus.shopping.flight_offers_search.get(**params)
        return response.data
    except ResponseError as error:
        print(f"❌ Amadeus error: {error.response.body if hasattr(error, 'response') else error}")
        return []
# --------------------------------------
# 5. Sort offers based on user preference
# --------------------------------------
def sort_offers(offers, preference):
    if preference == "cheapest":
        return sorted(offers, key=lambda o: float(o['price']['total']))
    elif preference == "shortest":
        return sorted(offers, key=lambda o: duration_in_minutes(o['itineraries'][0]['duration']))
    elif preference == "direct":
        direct_fligts = [o for o in offers if all(len(i['segments']) == 1 for i in o['itineraries'])]
        if direct_fligts:
            return direct_fligts
        else:
            print("No direct flights found, returning all offers sorted by cheapest.")
            return sorted(offers, key=lambda o: float(o['price']['total']))
    return offers

# Helper to parse ISO8601 duration like "PT8H15M"
def duration_in_minutes(duration_str):
    import re
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", duration_str)
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    return hours * 60 + minutes

# --------------------------------------
# 6. Example usage
# --------------------------------------
if __name__ == "__main__":
    user_input = "I need a flight from Stuttgart to Istanbul on July 20, return July 30, prefer cheapest."

    a = Airports()
    a.load_airports("../data/airports.dat")
    args = extract_flight_request(user_input)
    print("🔍 Extracted:", args)

    origin = a.search_cities(args['origin'])
    destination = a.search_cities(args['destination'])

    o_iata = origin[0]['iata']
    d_iata = destination[2]['iata']

    print(f"Searching flights from {o_iata} to {d_iata}...") 

    offers = get_flight_details(
        origin=o_iata,
        destination=d_iata,
        departure_date=args['departure_date'],
        return_date=args.get('return_date'),
        preference=args.get('preference', 'cheapest')
    )
    print(f"Found {len(offers)} flight offers.")
    sorted_offers = sort_offers(offers, args.get('preference'))

    # Display top result
    for offer in sorted_offers:
        price = offer['price']['total']
        currency = offer['price']['currency']
        itineraries = offer['itineraries']

        print(f"💰 Price: {currency} {price}")

        for i, itinerary in enumerate(itineraries):
            flight_type = "Outbound" if i == 0 else "Return"
            print(f"  ✈️ {flight_type} Flight:")

            for segment in itinerary['segments']:
                departure = segment['departure']['at'] 
                arrival = segment['arrival']['at']
                airline = segment['carrierCode'] 
                dep_airport = segment['departure']['iataCode']
                arr_airport = segment['arrival']['iataCode']

                # Format times
                dep_time = departure.split('T')[1][:5]
                arr_time = arrival.split('T')[1][:5]

                print(f"    - {airline}: {dep_airport} {dep_time} ➔ {arr_airport} {arr_time}")

    print("---")
