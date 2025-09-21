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
                "daily_budget": {"budget": "$40-80", "mid_range": "$80-150", "luxury": "$150-300"},
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

    def _run(self, query: str) -> str:
        """Create a comprehensive, personalized travel plan based on destination and preferences"""
        
        # Parse the query to extract information
        query_lower = query.lower()
        
        # Extract destination
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
        plan = self._generate_personalized_plan(
            dest_data, days, preferences, weather_info, today
        )
        
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
    
    def _extract_weather(self, query: str) -> str:
        """Extract weather information from query"""
        if "weather" in query.lower():
            # Find weather section
            parts = query.split("weather")
            if len(parts) > 1:
                weather_part = parts[1].split(",")[0].split(".")[0]
                return weather_part.strip(": ")
        return "Pleasant weather conditions"
    
    def _generate_personalized_plan(self, dest_data: Dict, days: int, preferences: List[str], weather: str, today) -> str:
        """Generate a comprehensive personalized travel plan"""
        
        plan = f"""
🌟 **PERSONALIZED {days}-DAY TRAVEL PLAN FOR {dest_data['name'].upper()}, {dest_data['country'].upper()}**

📅 **TRIP OVERVIEW:**
- 🏙️ Destination: {dest_data['name']}, {dest_data['country']}
- ⏰ Duration: {days} days
- 💰 Currency: {dest_data['currency']}
- 🗣️ Language: {dest_data['language']}
- 🌤️ Current Weather: {weather}
- 📆 Planning Date: {today.strftime("%B %d, %Y")}
- 🎯 Your Interests: {', '.join(preferences).title()}

"""
        
        # Generate day-by-day itinerary based on preferences
        plan += self._generate_daily_itinerary(dest_data, days, preferences)
        
        # Add accommodation recommendations
        plan += self._generate_accommodation_section(dest_data)
        
        # Add cuisine section with local specialties
        plan += self._generate_cuisine_section(dest_data)
        
        # Add personalized budget breakdown
        plan += self._generate_budget_section(dest_data, days)
        
        # Add transportation info
        plan += self._generate_transportation_section(dest_data)
        
        # Add preference-specific recommendations
        plan += self._generate_preference_recommendations(dest_data, preferences)
        
        # Add practical information
        plan += self._generate_practical_info(dest_data, weather)
        
        return plan
    
    def _generate_daily_itinerary(self, dest_data: Dict, days: int, preferences: List[str]) -> str:
        """Generate personalized daily itinerary based on preferences"""
        itinerary = "🗓️ **PERSONALIZED DAILY ITINERARY:**\n\n"
        
        # Get relevant attractions based on preferences
        attractions = self._get_preference_based_attractions(dest_data, preferences)
        
        for day in range(1, days + 1):
            itinerary += f"**DAY {day}:**\n"
            
            # Distribute attractions across days
            day_attractions = self._distribute_attractions_for_day(attractions, day, days)
            
            itinerary += "**Morning (9:00-12:00):**\n"
            if day_attractions.get("morning"):
                attr = day_attractions["morning"]
                itinerary += f"- 🎯 Visit {attr['name']} ({attr.get('area', 'Central area')})\n"
                itinerary += f"  Duration: {attr.get('duration', '2-3 hours')}\n"
            
            itinerary += "\n**Lunch (12:00-14:00):**\n"
            if dest_data.get("local_cuisine"):
                local_dish = dest_data["local_cuisine"][min(day-1, len(dest_data["local_cuisine"])-1)]
                itinerary += f"- 🍽️ Try {local_dish['dish']} at {local_dish['where']}\n"
            
            itinerary += "\n**Afternoon (14:00-18:00):**\n"
            if day_attractions.get("afternoon"):
                attr = day_attractions["afternoon"]
                itinerary += f"- 🎯 Explore {attr['name']} ({attr.get('area', 'Central area')})\n"
                itinerary += f"  Duration: {attr.get('duration', '2-3 hours')}\n"
            
            itinerary += "\n**Evening (18:00-21:00):**\n"
            if "nightlife" in preferences and dest_data.get("nightlife"):
                night_spot = dest_data["nightlife"][min(day-1, len(dest_data["nightlife"])-1)]
                itinerary += f"- 🌃 Experience {night_spot['name']} - {night_spot['type']} in {night_spot['area']}\n"
            else:
                itinerary += f"- 🌆 Evening stroll and dinner in local area\n"
            
            itinerary += "\n"
        
        return itinerary
    
    def _get_preference_based_attractions(self, dest_data: Dict, preferences: List[str]) -> List[Dict]:
        """Get attractions based on user preferences"""
        attractions = []
        
        # Add landmarks (always include some)
        attractions.extend(dest_data.get("landmarks", [])[:4])
        
        # Add preference-specific attractions
        if "museums" in preferences:
            attractions.extend(dest_data.get("museums", []))
        
        if "nightlife" in preferences:
            attractions.extend(dest_data.get("nightlife", []))
        
        # If no specific preferences, add a mix
        if not any(pref in ["museums", "nightlife", "nature"] for pref in preferences):
            attractions.extend(dest_data.get("museums", [])[:2])
        
        return attractions
    
    def _distribute_attractions_for_day(self, attractions: List[Dict], day: int, total_days: int) -> Dict:
        """Distribute attractions across morning and afternoon for a specific day"""
        day_index = (day - 1) * 2  # 2 attractions per day
        
        result = {}
        if day_index < len(attractions):
            result["morning"] = attractions[day_index]
        
        if day_index + 1 < len(attractions):
            result["afternoon"] = attractions[day_index + 1]
        
        return result
    
    def _generate_accommodation_section(self, dest_data: Dict) -> str:
        """Generate accommodation recommendations"""
        budget = dest_data.get("daily_budget", {})
        
        return f"""
🏨 **ACCOMMODATION RECOMMENDATIONS:**

**Luxury Options ({budget.get('luxury', '$150-300')}/night):**
- Premium hotels in {dest_data['name']} city center
- 5-star amenities, concierge services, spa facilities
- Top locations with easy access to major attractions

**Mid-Range Options ({budget.get('mid_range', '$80-150')}/night):**
- Boutique hotels or quality chains in central areas
- Modern amenities, great location, excellent value
- Perfect balance of comfort and affordability

**Budget Options ({budget.get('budget', '$40-80')}/night):**
- Clean hostels, guesthouses, or budget hotels
- Safe locations with basic amenities
- Great for meeting other travelers and saving money

"""
    
    def _generate_cuisine_section(self, dest_data: Dict) -> str:
        """Generate cuisine section with local specialties"""
        cuisine_section = """
🍽️ **LOCAL CULINARY EXPERIENCES:**

**Must-Try Local Specialties:**
"""
        
        if dest_data.get("local_cuisine"):
            for dish_info in dest_data["local_cuisine"]:
                cuisine_section += f"- 🥘 **{dish_info['dish']}** - Available at {dish_info['where']}\n"
        else:
            cuisine_section += "- Local traditional dishes and international cuisine\n"
        
        cuisine_section += f"""
**Dining Recommendations:**
- 🍴 Fine dining for special occasions
- 🏠 Family-run local restaurants for authentic cuisine  
- 🛒 Local markets and street food for budget-friendly meals
- ☕ Cafés and bistros for casual dining with atmosphere

"""
        return cuisine_section
    
    def _generate_budget_section(self, dest_data: Dict, days: int) -> str:
        """Generate budget breakdown with local currency"""
        budget = dest_data.get("daily_budget", {})
        transport = dest_data.get("transportation", {})
        
        # Calculate total costs
        budget_total = self._calculate_total_costs(budget, days)
        mid_total = self._calculate_total_costs(budget, days, "mid_range")
        luxury_total = self._calculate_total_costs(budget, days, "luxury")
        
        return f"""
💰 **ESTIMATED BUDGET BREAKDOWN ({dest_data['currency']}):**

**Daily Costs (per person):**
- 🏨 Accommodation: {budget.get('budget', '$40-80')} - {budget.get('luxury', '$150-300')}/night
- 🍽️ Meals: 25-50% of accommodation cost (street food to fine dining)
- 🎫 Activities & Attractions: 15-35% of daily budget
- 🚌 Local Transportation: {transport.get('day_pass', transport.get('oyster_day', transport.get('metro_day', '$10-20')))} for day passes
- 🛍️ Shopping & Miscellaneous: 10-30% of daily budget

**Total {days}-Day Trip Estimates:**
- 💵 Budget Trip: {budget_total}
- 💎 Mid-Range Trip: {mid_total}  
- 👑 Luxury Trip: {luxury_total}

"""
    
    def _calculate_total_costs(self, budget: Dict, days: int, tier: str = "budget") -> str:
        """Calculate total trip costs"""
        daily_base = budget.get(tier, "$60")
        # Extract number from string like "$40-80" or "€50-80"
        if "-" in daily_base:
            amount = daily_base.split("-")[1]
        else:
            amount = daily_base
        
        # Extract currency symbol and number
        currency = amount[0] if not amount[0].isdigit() else "$"
        number = ''.join(filter(str.isdigit, amount))
        
        if number:
            total = int(number) * days
            return f"{currency}{total}"
        
        return f"{currency}{days * 80}"
    
    def _generate_transportation_section(self, dest_data: Dict) -> str:
        """Generate transportation information"""
        transport = dest_data.get("transportation", {})
        
        return f"""
🚗 **TRANSPORTATION & GETTING AROUND:**

**Public Transportation:**
- 🚇 Day passes: {transport.get('day_pass', transport.get('oyster_day', transport.get('metro_day', 'Local transport passes available')))}
- 🚌 Extensive bus and metro/subway networks
- 📱 Use local transport apps for real-time info

**Airport Connections:**
- ✈️ Airport to city center: {transport.get('airport_train', transport.get('airport_express', '$15-30'))}
- 🚖 Taxi from airport: {transport.get('taxi_base', 'Varies by distance')} base fare + distance

**Getting Around:**
- 🚶 Many attractions walkable in city center
- 🚲 Bike sharing systems available
- 🚕 Taxis and ride-sharing services widely available

"""
    
    def _generate_preference_recommendations(self, dest_data: Dict, preferences: List[str]) -> str:
        """Generate recommendations based on user preferences"""
        recommendations = """
🎯 **PERSONALIZED RECOMMENDATIONS BASED ON YOUR INTERESTS:**

"""
        
        if "museums" in preferences:
            recommendations += "**🏛️ Museum Lover's Special:**\n"
            for museum in dest_data.get("museums", []):
                recommendations += f"- {museum['name']} - {museum['specialty']} ({museum['area']})\n"
            recommendations += "\n"
        
        if "nightlife" in preferences:
            recommendations += "**🌃 Nightlife Enthusiast:**\n"
            for spot in dest_data.get("nightlife", []):
                recommendations += f"- {spot['name']} - {spot['type']} in {spot['area']}\n"
            recommendations += "\n"
        
        if "food" in preferences:
            recommendations += "**🍴 Foodie Paradise:**\n"
            for dish in dest_data.get("local_cuisine", []):
                recommendations += f"- Must try {dish['dish']} at {dish['where']}\n"
            recommendations += "\n"
        
        return recommendations
    
    def _generate_practical_info(self, dest_data: Dict, weather: str) -> str:
        """Generate practical travel information"""
        return f"""
📱 **PRACTICAL TRAVEL INFORMATION:**

**Essential Details:**
- 🌍 Language: {dest_data['language']} (English widely understood in tourist areas)
- 💱 Currency: {dest_data['currency']}
- ⏰ Timezone: {dest_data['timezone']}
- 🌤️ Current Weather: {weather}

**What to Pack:**
- 📄 Passport/ID and travel documents
- 💳 Credit cards and some local cash
- 🔌 Universal power adapter
- 👕 Weather-appropriate clothing
- 👟 Comfortable walking shoes
- 📱 Phone with local SIM or international plan

**Cultural Tips:**
- 🤝 Learn basic greetings in {dest_data['language']}
- 💡 Research local customs and etiquette
- 📸 Ask permission before photographing people
- 💰 Understand local tipping practices

**Safety & Connectivity:**
- 🚨 Save emergency numbers in your phone
- 📍 Share your itinerary with someone at home
- 🌐 Free Wi-Fi available at most cafés and hotels
- 🏥 Locate nearest hospital/pharmacy for emergencies

This personalized itinerary for {dest_data['name']} is tailored to your interests in {', '.join(preferences)}. Enjoy your amazing journey! ✈️🌍
"""

def create_travel_planning_tool():
    """Create the travel planning tool"""
    return TravelPlanningTool()