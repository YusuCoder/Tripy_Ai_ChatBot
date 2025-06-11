import requests
import os
from typing import Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

class WeatherInput(BaseModel):
    city: str = Field(description="City name to get the weather for")
    country_code: Optional[str] = Field(default=None, description="2-letter country code (optional)")

class WeatherTool(BaseTool):
    name: str = "get_weather"
    description: str = """Get current weather and 5-day forecast for a specified city.
    Useful for travel planning to recommend appropriate activities and clothing.
    Input should be a city name, optionally with a country code."""
    args_schema: Type[BaseModel] = WeatherInput

    def _run(self, city: str, country_code: Optional[str] = None) -> str:
        """Execute the weather lookup"""
        try:
            api_key = os.getenv("WEATHER_API_KEY")
            if not api_key:
                return "Weather service unavailable - API key not configured."

            query = city
            if country_code:
                query = f"{city},{country_code}"

            current_url = f"http://api.openweathermap.org/data/2.5/weather"
            current_params = {
                "q": query,
                "appid": api_key,
                "units": "metric"
            }

            current_response = requests.get(current_url, params=current_params)

            if current_response.status_code != 200:
                return f"Could not get weather for {city}. Please check the city name again."

            current_data = current_response.json()
            forecast_url = f"http://api.openweathermap.org/data/2.5/forecast"
            forecast_params = {
                "q": query,
                "appid": api_key,
                "units": "metric"
            }

            forecast_response = requests.get(forecast_url, params=forecast_params)


            result = self._format_weather_info(current_data, forecast_response.json() if forecast_response.status_code == 200 else None)
            return result

        except Exception as e:
            return f"An error occurred while fetching weather data: {str(e)}"
        
    async def _arun(self, city: str, country_code: Optional[dict] = None) -> str:
        """Async version, just call the sync version for now"""
        return self._run(city, country_code)

    def _format_weather_info(self, current_data, forecast_data: Optional[dict] = None) -> str:
        """Format weather data into a readable string"""
    
        cityname = current_data['name']
        country = current_data['sys']['country']
        temperature = round(current_data['main']['temp'])
        feels_like = round(current_data['main']['feels_like'])
        description = current_data['weather'][0]['description'].title()
        humidity = current_data['main']['humidity']
    
    
        result = f"Current weather in {cityname}, {country}:\n\n"
        result += f"Temperature: {temperature}°C (Feels like: {feels_like}°C)\n"
        result += f"Condition: {description}\n"
        result += f"Humidity: {humidity}%\n"
    
        if forecast_data:
            result += "\n5-day Forecast:\n"
    
            day_forecasts = {}
            for item in forecast_data['list'][:15]:
                date = item['dt_txt'].split(' ')[0]
                if date not in day_forecasts:
                    day_forecasts[date] = {
                        'temp_min': item['main']['temp'],
                        'temp_max': item['main']['temp'],
                        'description': item['weather'][0]['description'],
                    }
                else:
                    day_forecasts[date]['temp_min'] = min(day_forecasts[date]['temp_min'], item['main']['temp'])
                    day_forecasts[date]['temp_max'] = max(day_forecasts[date]['temp_max'], item['main']['temp'])
            
            for date, data in list(day_forecasts.items())[:5]:
                temp_min = round(data['temp_min'])
                temp_max = round(data['temp_max'])
                description = data['description'].title()
                result += f"{date}: {temp_min}°C - {temp_max}°C, {description}\n"
        
        result += "\nTravel Tips:\n"
        if temperature < 10:
            result += " * Pack warm clothing and consider indoor activities.\n"
            result += " * Great for indoor activities, museums, or cozy cafes.\n"
        elif temperature > 25:
            result += " * Pack light and breathable clothing.\n"
            result += " * Perfect for outdoor activities like hiking or sightseeing.\n"
            result += " * Stay hydrated and use sunscreen.\n"
        else:
            result += " * Comfortable weather for most activities.\n"
            result += " * Pack layers for changing temperatures.\n"
    
        if humidity > 70:
            result += " * High humidity - dress for confort.\n"
        
        return result

def create_weather_tool():
    """Create and return the weather tool"""
    return WeatherTool()