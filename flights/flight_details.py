from amadeus import Client, ResponseError
from dotenv import load_dotenv
from openai import OpenAI
import os
import openai
import json
import spacy
from typing import Optional, Dict

load_dotenv(dotenv_path="../config/.env")
nlp = spacy.load("en_core_web_sm")


function_schema = {
    "name": "extract_flight_request",
    "description": "Extracts flight search details from user's natural language query",
    "parameters": {
        "type": "object",
        "properties": {
            "origin": {"type": "string", "description": "Departure airport or city (e.g. JFK or New York)"},
            "destination": {"type": "string", "description": "Arrival airport or city (e.g. LAX or Los Angeles)"},
            "departure_date": {"type": "string", "description": "Departure date in YYYY-MM-DD"},
            "return_date": {"type": "string", "description": "Return date in YYYY-MM-DD", "nullable": True},
            "preference": {
                "type": "string",
                "enum": ["cheapest", "shortest", "direct"],
                "description": "Flight preference"
            }
        },
        "required": ["origin", "destination", "departure_date"]
    }
}



def get_flight_details(origin: str, destination: str, departure_date: str, return_date: Optional[str] = None, preference: str = "cheapest"):
    """
    Fetches flight offers using Amadeus API
    """
    amadeus = Client(client_id=os.getenv("AMADEUS_API_KEY"), client_secret=os.getenv("AMADEUS_API_SECRET"))
    try:
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            returnDate=return_date,
            adults=1,
            max=5,
        )
        offers = response.data
        return offers
    except ResponseError as error:
        print(f"❌ Amadeus error: {error}")
        return []



def extract_flight_request(user_input):
    client = OpenAI(api_key=os.getenv("API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[{"role": "user", "content": user_input}],
        functions=[function_schema],
        function_call={"name": "extract_flight_request"},
    )
    args = json.loads(response.choices[0].message.function_call.arguments)
    return args


def sort_offers(offers, preference):
    if preference == "cheapest":
        return sorted(offers, key=lambda o: float(o['price']['total']))
    elif preference == "shortest":
        return sorted(offers, key=lambda o: int(o['itineraries'][0]['duration'].replace("PT", "").replace("H", "").replace("M", "")))
    elif preference == "direct":
        return [o for o in offers if all(len(i['segments']) == 1 for i in o['itineraries'])]
    return offers


user_input = "I need a flight from New York to Rome on July 20, return July 30, prefer cheapest."
# print("OpenAI API Key:", os.getenv("API_KEY"))
args = extract_flight_request(user_input)

offers = get_flight_details(
    origin=args['origin'],
    destination=args['destination'],
    departure_date=args['departure_date'],
    return_date=args.get('return_date'),
    preference=args.get('preference', 'cheapest')
)

sorted_offers = sort_offers(offers, args.get('preference'))






# def get_offes_summary():
#     """Summarizes flight offers."""
#     offers = get_flight_details()

#     price = float(offers['price']['total'])
#     itinerary = offers['itineraries'][0]
#     segments = itinerary['segments']
#     duration = itinerary['duration']
#     direct = len(segments) == 1
#     airline = segments[0]['carrierCode']
#     departure_time = segments[0]['departure']['at']
#     arrival_time = segments[-1]['arrival']['at']

#     return {
#         'price': price,
#         'itinerary': itinerary,
#         'duration': duration,
#         'direct': direct,
#         'airline': airline,
#         'departure_time': departure_time,
#         'arrival_time': arrival_time,
#         'raw': offers
#     }


# function_schema = {
#     "name": "extract_flight_request",
#     "description": "Extracts flight search details from user's natural language query",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "origin": {"type": "string", "description": "Departure airport or city (e.g. JFK or New York)"},
#             "destination": {"type": "string", "description": "Arrival airport or city (e.g. LAX or Los Angeles)"},
#             "departure_date": {"type": "string", "description": "Departure date in YYYY-MM-DD"},
#             "return_date": {"type": "string", "description": "Return date in YYYY-MM-DD", "nullable": True},
#             "preference": {
#                 "type": "string",
#                 "enum": ["cheapest", "shortest", "direct"],
#                 "description": "Flight preference"
#             }
#         },
#         "required": ["origin", "destination", "departure_date"]
#     }
# }


# def extract_flight_request(user_input):
#     response = openai.ChatCompletion.create(
#         model="gpt-4-1106-preview",
#         messages=[{"role": "user", "content": user_input}],
#         functions=[function_schema],
#         function_call={"name": "extract_flight_request"},
#     )
#     args = json.loads(response.choices[0].message.function_call.arguments)

#     return args






# def extract_partial_info(user_input):
#     """Extracts partial flight information from user's input."""
#     prompt = f"""
#     Extract available travel details from this input.
#     Return a JSON with any of the following keys of available:
#     destination, origin, date, duration, adults, budget, preferences.

#     Input: "{user_input}"
#     Example: {{"destination": "Paris", "departure_date": "2025-06-25"}}       
# """
    
#     res = openai.ChatCompletion.create( ... )
#     return json.loads(res.choices[0].message.content)


# def extract_travel_details_nlp(text: str):
#     doc = nlp(text)
#     details = {
#         "origin": None,
#         "destination": None,
#         "departure_date": None,
#         "return_date": None,
#         "budget": None,
#     }

#     # Named Entity Recognition
#     for ent in doc.ents:
#         if ent.label_ == "GPE":  # Geo-political entity
#             if not details["destination"]:
#                 details["destination"] = ent.text
#             elif not details["origin"]:
#                 details["origin"] = ent.text

#         elif ent.label_ == "DATE":
#             if not details["departure_date"]:
#                 details["departure_date"] = ent.text
#             else:
#                 details["return_date"] = ent.text

#         elif ent.label_ == "MONEY":
#             details["budget"] = ent.text

#     return details
