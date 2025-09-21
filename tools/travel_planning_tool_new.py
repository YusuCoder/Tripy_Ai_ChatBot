from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type, Dict, List
import datetime
import json

class TravelPlanInput(BaseModel):
    query: str = Field(description="Travel planning request including destination, duration, preferences, and weather information")

class TravelPlanningTool(BaseTool):
    name: str = "create_travel_plan"
    description: str = """Create a comprehensive, personalized travel plan with location-specific attractions and activities.
    MANDATORY: Use this tool AFTER checking weather and collecting user preferences.
    Input should include destination, duration, user preferences, and current weather conditions.
    Example: '7-day trip to Japan, preferences: museums and temples, current weather is 29°C with broken clouds'
    This tool creates PERSONALIZED travel plans based on actual landmarks and user interests."""
    args_schema: Type[BaseModel] = TravelPlanInput

    def _get_destination_data(self) -> Dict:
        """Load comprehensive destination data with real landmarks, attractions, and local info"""
        return {
            "tokyo": {
                "name": "Tokyo",
                "country": "Japan",
                "currency": "JPY (¥)",
                "language": "Japanese",
                "timezone": "JST (UTC+9)",
                "landmarks": [
                    {"name": "Senso-ji Temple", "type": "temple", "area": "Asakusa", "duration": "2-3 hours"},
                    {"name": "Tokyo Skytree", "type": "observation", "area": "Sumida", "duration": "2-3 hours"},
                    {"name": "Meiji Shrine", "type": "shrine", "area": "Shibuya", "duration": "1-2 hours"},
                    {"name": "Tsukiji Outer Market", "type": "market", "area": "Tsukiji", "duration": "2-3 hours"},
                    {"name": "Imperial Palace East Gardens", "type": "garden", "area": "Chiyoda", "duration": "2 hours"},
                    {"name": "Shibuya Crossing", "type": "landmark", "area": "Shibuya", "duration": "30 min"},
                    {"name": "Tokyo National Museum", "type": "museum", "area": "Ueno", "duration": "3-4 hours"},
                    {"name": "Roppongi Hills", "type": "shopping", "area": "Roppongi", "duration": "3-4 hours"}
                ],
                "museums": [
                    {"name": "Tokyo National Museum", "specialty": "Japanese art & history", "area": "Ueno"},
                    {"name": "Mori Art Museum", "specialty": "Contemporary art", "area": "Roppongi"},
                    {"name": "Edo-Tokyo Museum", "specialty": "Tokyo history", "area": "Sumida"},
                    {"name": "National Museum of Nature and Science", "specialty": "Science & nature", "area": "Ueno"}
                ],
                "nightlife": [
                    {"name": "Golden Gai", "type": "bar district", "area": "Shinjuku"},
                    {"name": "Roppongi nightlife", "type": "clubs & bars", "area": "Roppongi"},
                    {"name": "Kabukicho", "type": "entertainment district", "area": "Shinjuku"},
                    {"name": "Memory Lane (Omoide Yokocho)", "type": "yakitori alleys", "area": "Shinjuku"}
                ],
                "local_cuisine": [
                    {"dish": "Sushi", "where": "Tsukiji area or high-end restaurants"},
                    {"dish": "Ramen", "where": "Ichiran, Ippudo, or local ramen shops"},
                    {"dish": "Tempura", "where": "Daikokuya (Asakusa) or upscale restaurants"},
                    {"dish": "Yakitori", "where": "Memory Lane or Torikizoku chains"},
                    {"dish": "Monjayaki", "where": "Tsukishima (local Tokyo specialty)"}
                ],
                "daily_budget": {"budget": "¥6,000-12,000", "mid_range": "¥12,000-20,000", "luxury": "¥20,000-40,000"},
                "transportation": {"day_pass": "¥800 (Tokyo Metro)", "taxi_base": "¥420", "airport_train": "¥160-400"}
            },
            "paris": {
                "name": "Paris", 
                "country": "France",
                "currency": "EUR (€)",
                "language": "French",
                "timezone": "CET (UTC+1)",
                "landmarks": [
                    {"name": "Eiffel Tower", "type": "landmark", "area": "7th arrondissement", "duration": "2-3 hours"},
                    {"name": "Louvre Museum", "type": "museum", "area": "1st arrondissement", "duration": "4-6 hours"},
                    {"name": "Notre-Dame Cathedral", "type": "cathedral", "area": "4th arrondissement", "duration": "1-2 hours"},
                    {"name": "Arc de Triomphe", "type": "monument", "area": "8th arrondissement", "duration": "1 hour"},
                    {"name": "Sacré-Cœur Basilica", "type": "basilica", "area": "Montmartre", "duration": "1-2 hours"},
                    {"name": "Seine River Cruise", "type": "cruise", "area": "Multiple", "duration": "1-2 hours"},
                    {"name": "Champs-Élysées", "type": "avenue", "area": "8th arrondissement", "duration": "2-3 hours"},
                    {"name": "Montmartre District", "type": "neighborhood", "area": "18th arrondissement", "duration": "3-4 hours"}
                ],
                "museums": [
                    {"name": "Louvre Museum", "specialty": "World's largest art museum", "area": "1st arrondissement"},
                    {"name": "Musée d'Orsay", "specialty": "Impressionist art", "area": "7th arrondissement"},
                    {"name": "Centre Pompidou", "specialty": "Modern art", "area": "4th arrondissement"},
                    {"name": "Rodin Museum", "specialty": "Sculptures", "area": "7th arrondissement"}
                ],
                "nightlife": [
                    {"name": "Latin Quarter", "type": "bars & cafes", "area": "5th arrondissement"},
                    {"name": "Marais District", "type": "trendy bars", "area": "3rd/4th arrondissement"},
                    {"name": "Pigalle", "type": "cabaret & clubs", "area": "18th arrondissement"},
                    {"name": "Seine River evening cruise", "type": "romantic cruise", "area": "Multiple"}
                ],
                "local_cuisine": [
                    {"dish": "Croissants & Pain au Chocolat", "where": "Local boulangeries"},
                    {"dish": "Coq au Vin", "where": "Traditional bistros"},
                    {"dish": "French Onion Soup", "where": "Café de Flore or Les Deux Magots"},
                    {"dish": "Macarons", "where": "Ladurée or Pierre Hermé"},
                    {"dish": "Escargot", "where": "L'Ami Jean or traditional restaurants"}
                ],
                "daily_budget": {"budget": "€50-80", "mid_range": "€80-150", "luxury": "€150-400"},
                "transportation": {"metro_day": "€7.50", "taxi_base": "€2.60", "airport_train": "€10-25"}
            },
            "london": {
                "name": "London",
                "country": "United Kingdom", 
                "currency": "GBP (£)",
                "language": "English",
                "timezone": "GMT (UTC+0)",
                "landmarks": [
                    {"name": "Big Ben & Parliament", "type": "landmark", "area": "Westminster", "duration": "1-2 hours"},
                    {"name": "Tower of London", "type": "historic castle", "area": "Tower Hamlets", "duration": "3-4 hours"},
                    {"name": "Buckingham Palace", "type": "palace", "area": "Westminster", "duration": "1-2 hours"},
                    {"name": "London Eye", "type": "observation wheel", "area": "South Bank", "duration": "1 hour"},
                    {"name": "Tower Bridge", "type": "bridge", "area": "Tower Hamlets", "duration": "1 hour"},
                    {"name": "Westminster Abbey", "type": "abbey", "area": "Westminster", "duration": "2 hours"},
                    {"name": "St. Paul's Cathedral", "type": "cathedral", "area": "City of London", "duration": "2 hours"},
                    {"name": "Hyde Park", "type": "park", "area": "Central London", "duration": "2-3 hours"}
                ],
                "museums": [
                    {"name": "British Museum", "specialty": "World history & artifacts", "area": "Bloomsbury"},
                    {"name": "Tate Modern", "specialty": "Modern & contemporary art", "area": "South Bank"},
                    {"name": "National Gallery", "specialty": "European paintings", "area": "Trafalgar Square"},
                    {"name": "Victoria & Albert Museum", "specialty": "Decorative arts", "area": "South Kensington"}
                ],
                "nightlife": [
                    {"name": "Soho", "type": "bars & clubs", "area": "West End"},
                    {"name": "Shoreditch", "type": "trendy bars", "area": "East London"},
                    {"name": "Covent Garden", "type": "pubs & entertainment", "area": "West End"},
                    {"name": "Thames riverside pubs", "type": "traditional pubs", "area": "Multiple"}
                ],
                "local_cuisine": [
                    {"dish": "Fish & Chips", "where": "Poppies or local chippies"},
                    {"dish": "Sunday Roast", "where": "Traditional pubs"},
                    {"dish": "Afternoon Tea", "where": "Fortnum & Mason or The Ritz"},
                    {"dish": "Bangers & Mash", "where": "gastropubs"},
                    {"dish": "Pie & Mash", "where": "F. Cooke or traditional pie shops"}
                ],
                "daily_budget": {"budget": "£40-70", "mid_range": "£70-120", "luxury": "£120-300"},
                "transportation": {"oyster_day": "£12.70", "taxi_base": "£2.60", "airport_train": "£15-25"}
            }
        }
    
    def _run(self, query: str) -> str:
        """Create a comprehensive, personalized travel plan based on destination and preferences"""
        
        # Parse the query to extract information
        destination_info = self._determine_destination(query)
        dest_data = self._get_destination_info(destination_info["name"])
        
        # Extract duration
        days = self._extract_duration(query)
        
        # Extract user preferences
        preferences = self._extract_preferences(query)
        
        # Extract weather info
        weather_info = self._extract_weather(query)
        
        today = datetime.date.today()
        
        # Generate personalized travel plan
        plan = f"""
🌟 **PERSONALIZED {days}-DAY TRAVEL PLAN FOR {dest_data['name'].upper()}, {dest_data['country'].upper()}**

📅 **TRIP OVERVIEW:**
- 🏙️ Destination: {dest_data['name']}, {dest_data['country']}
- ⏰ Duration: {days} days
- 💰 Currency: {dest_data['currency']}
- 🗣️ Language: {dest_data['language']}
- 🌤️ Current Weather: {weather_info}
- 📆 Planning Date: {today.strftime("%B %d, %Y")}
- 🎯 Your Interests: {', '.join(preferences).title()}

🗓️ **PERSONALIZED DAILY ITINERARY:**

"""
        
        # Generate preference-based daily activities
        for day in range(1, days + 1):
            plan += f"**DAY {day}:**\n"
            
            # Morning activity based on preferences
            morning_activity = self._get_activity_for_time(dest_data, preferences, "morning", day)
            plan += f"**Morning (9:00-12:00):**\n- 🎯 {morning_activity}\n\n"
            
            # Lunch recommendation
            if dest_data.get("local_cuisine") and len(dest_data["local_cuisine"]) > 0:
                lunch_idx = (day - 1) % len(dest_data["local_cuisine"])
                local_dish = dest_data["local_cuisine"][lunch_idx]
                plan += f"**Lunch (12:00-14:00):**\n- 🍽️ Try {local_dish['dish']} at {local_dish['where']}\n\n"
            
            # Afternoon activity
            afternoon_activity = self._get_activity_for_time(dest_data, preferences, "afternoon", day)
            plan += f"**Afternoon (14:00-18:00):**\n- 🎯 {afternoon_activity}\n\n"
            
            # Evening activity
            evening_activity = self._get_activity_for_time(dest_data, preferences, "evening", day)
            plan += f"**Evening (18:00-21:00):**\n- 🌃 {evening_activity}\n\n"
        
        # Add budget section with local currency
        plan += f"""
💰 **ESTIMATED BUDGET BREAKDOWN ({dest_data['currency']}):**

**Daily Costs (per person):**
- 🏨 Accommodation: {dest_data['daily_budget']['budget']} - {dest_data['daily_budget']['luxury']}/night
- 🍽️ Meals: Local restaurants to fine dining
- 🎫 Activities & Attractions: Major sites and experiences
- 🚌 Local Transportation: {dest_data['transportation'].get('day_pass', dest_data['transportation'].get('oyster_day', dest_data['transportation'].get('metro_day', 'Day passes available')))}

"""
        
        # Add preference-specific recommendations
        if "museums" in preferences:
            plan += "🏛️ **MUSEUM RECOMMENDATIONS (Based on Your Interest):**\n"
            for museum in dest_data.get("museums", []):
                plan += f"- **{museum['name']}** - {museum['specialty']} ({museum['area']})\n"
            plan += "\n"
        
        if "nightlife" in preferences:
            plan += "🌃 **NIGHTLIFE SPOTS (Based on Your Interest):**\n"
            for spot in dest_data.get("nightlife", []):
                plan += f"- **{spot['name']}** - {spot['type']} in {spot['area']}\n"
            plan += "\n"
        
        # Add practical information
        plan += f"""
📱 **PRACTICAL TRAVEL INFORMATION:**

**Essential Details:**
- 🌍 Language: {dest_data['language']} (English widely understood in tourist areas)
- 💱 Currency: {dest_data['currency']}
- ⏰ Timezone: {dest_data['timezone']}
- 🌤️ Weather: {weather_info}

**Getting Around:**
- 🚇 Public Transport: {dest_data['transportation'].get('day_pass', dest_data['transportation'].get('oyster_day', dest_data['transportation'].get('metro_day', 'Local transport available')))}
- 🚖 Taxis: {dest_data['transportation'].get('taxi_base', 'Available throughout the city')} base fare

This personalized {days}-day itinerary for {dest_data['name']} is tailored specifically to your interests in {', '.join(preferences)}! 

🎉 Have an amazing journey! ✈️🌍
"""
        
        return plan
    
    def _determine_destination(self, query: str) -> Dict:
        """Determine destination from query"""
        query_lower = query.lower()
        destination_data = self._get_destination_data()
        
        # Check for destinations in our database
        for key, data in destination_data.items():
            if key in query_lower or data["name"].lower() in query_lower:
                return {"name": data["name"], "key": key}
        
        # Extract from common patterns
        destination_keywords = ["to", "in", "visit", "visiting", "trip to"]
        words = query.split()
        
        for i, word in enumerate(words):
            if word.lower().strip(",") in destination_keywords:
                if i + 1 < len(words):
                    dest_name = words[i + 1].strip(".,!?").title()
                    return {"name": dest_name, "key": dest_name.lower()}
        
        return {"name": "Paris", "key": "paris"}  # Default
    
    def _get_destination_info(self, destination: str) -> Dict:
        """Get destination information based on destination string"""
        dest_lower = destination.lower()
        destination_data = self._get_destination_data()
        
        # Check for exact matches first
        for key, data in destination_data.items():
            if key in dest_lower or data["name"].lower() in dest_lower:
                return data
        
        # Default fallback with generic structure
        return {
            "name": destination,
            "country": "Unknown",
            "currency": "Local currency",
            "language": "Local language",
            "timezone": "Local time",
            "landmarks": [],
            "museums": [],
            "nightlife": [],
            "local_cuisine": [],
            "daily_budget": {"budget": "$30-60", "mid_range": "$60-120", "luxury": "$120-250"},
            "transportation": {"local_transport": "Varies by location"}
        }
    
    def _extract_duration(self, query: str) -> int:
        """Extract trip duration from query"""
        words = query.split()
        for i, word in enumerate(words):
            if word.isdigit():
                return int(word)
            elif "day" in word:
                num = ''.join(filter(str.isdigit, word))
                if num:
                    return int(num)
        return 7  # default
    
    def _extract_preferences(self, query: str) -> List[str]:
        """Extract user preferences from the query"""
        preferences = []
        query_lower = query.lower()
        
        # Preference mapping
        pref_keywords = {
            "museums": ["museum", "art", "history", "culture", "gallery", "exhibition"],
            "nightlife": ["night", "bar", "club", "party", "entertainment", "drinks", "nightlife"],
            "nature": ["park", "garden", "nature", "outdoor", "hiking", "walking"],
            "food": ["food", "restaurant", "cuisine", "eating", "dining", "culinary"],
            "shopping": ["shopping", "market", "mall", "boutique", "souvenir"],
            "architecture": ["architecture", "building", "cathedral", "church", "temple"],
            "adventure": ["adventure", "activity", "sports", "thrill", "exciting"],
            "relaxation": ["relax", "spa", "peaceful", "quiet", "calm", "leisure"],
            "photography": ["photo", "instagram", "scenic", "views", "picturesque"],
            "budget": ["budget", "cheap", "affordable", "free", "low cost"]
        }
        
        for pref_type, keywords in pref_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                preferences.append(pref_type)
        
        return preferences if preferences else ["general"]
    
    def _extract_weather(self, query: str) -> str:
        """Extract weather information from query"""
        if "weather" in query.lower():
            # Find weather section
            parts = query.split("weather")
            if len(parts) > 1:
                weather_part = parts[1].split(",")[0].split(".")[0]
                return weather_part.strip(": ")
        return "Pleasant weather conditions"
    
    def _get_activity_for_time(self, dest_data: Dict, preferences: List[str], time_of_day: str, day: int) -> str:
        """Get activity recommendation based on time of day and preferences"""
        
        if time_of_day == "morning":
            if "museums" in preferences and dest_data.get("museums"):
                museum_idx = (day - 1) % len(dest_data["museums"])
                museum = dest_data["museums"][museum_idx]
                return f"Visit {museum['name']} - {museum['specialty']} ({museum['area']})"
            elif dest_data.get("landmarks"):
                landmark_idx = (day - 1) % len(dest_data["landmarks"])
                landmark = dest_data["landmarks"][landmark_idx]
                return f"Explore {landmark['name']} ({landmark['area']}) - {landmark.get('duration', '2-3 hours')}"
        
        elif time_of_day == "afternoon":
            if day <= len(dest_data.get("landmarks", [])):
                landmark = dest_data["landmarks"][day - 1]
                return f"Visit {landmark['name']} ({landmark['area']}) - {landmark.get('duration', '2-3 hours')}"
            else:
                return "Explore local neighborhoods and markets"
        
        elif time_of_day == "evening":
            if "nightlife" in preferences and dest_data.get("nightlife"):
                night_idx = (day - 1) % len(dest_data["nightlife"])
                nightspot = dest_data["nightlife"][night_idx]
                return f"Experience {nightspot['name']} - {nightspot['type']} in {nightspot['area']}"
            else:
                return "Dinner and evening stroll in the city center"
        
        return "Explore the local area"

def create_travel_planning_tool():
    """Create the travel planning tool"""
    return TravelPlanningTool()