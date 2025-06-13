import os
from typing import Optional, Type
from langchain.tools import BaseTool
from langchain_community.utilities import OpenWeatherMapAPIWrapper
from pydantic import BaseModel, Field

class WeatherInput(BaseModel):
    city: str = Field(description="City name to get the weather for")
    country_code: Optional[str] = Field(default=None, description="2-letter country code (optional)")

# Step 1: Create a subclass to extend OpenWeatherMapAPIWrapper
class CustomWeatherWrapper(OpenWeatherMapAPIWrapper):
    def get_current_weather_data(self, location: str):
        return self._call_api("weather", {"q": location, "units": "metric"})

    def get_forecast_data(self, location: str):
        return self._call_api("forecast", {"q": location, "units": "metric"})

    def format_weather(self, current_data, forecast_data):
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
            for item in forecast_data['list']:
                date = item['dt_txt'].split(' ')[0]
                if date not in day_forecasts:
                    day_forecasts[date] = {
                        'temp_min': item['main']['temp_min'],
                        'temp_max': item['main']['temp_max'],
                        'description': item['weather'][0]['description'],
                    }
                else:
                    day_forecasts[date]['temp_min'] = min(day_forecasts[date]['temp_min'], item['main']['temp_min'])
                    day_forecasts[date]['temp_max'] = max(day_forecasts[date]['temp_max'], item['main']['temp_max'])

            # Limit to next 5 days
            for date, data in list(day_forecasts.items())[:5]:
                temp_min = round(data['temp_min'])
                temp_max = round(data['temp_max'])
                description = data['description'].title()
                result += f"{date}: {temp_min}°C - {temp_max}°C, {description}\n"

        # Example travel tips based on temperature & humidity
        if temperature < 10:
            result += "\nTravel Tips:\n * Pack warm clothes and enjoy indoor activities.\n"
        elif temperature > 25:
            result += "\nTravel Tips:\n * Pack light clothes, stay hydrated, and use sunscreen.\n"
        else:
            result += "\nTravel Tips:\n * Comfortable weather, pack layers for changes.\n"

        if humidity > 70:
            result += " * High humidity, dress comfortably.\n"

        return result

    # Override run() to fetch and format both current + forecast data
    def run(self, location: str) -> str:
        current = self.get_current_weather_data(location)
        forecast = self.get_forecast_data(location)
        return self.format_weather(current, forecast)


# Step 2: Use the custom wrapper in your tool
class WeatherTool(BaseTool):
    name: str = "get_weather"
    description: str = """Get current weather and 5-day forecast with custom formatting."""
    args_schema: Type[BaseModel] = WeatherInput

    def _run(self, city: str, country_code: Optional[str] = None) -> str:
        try:
            wrapper = CustomWeatherWrapper()
            query = f"{city},{country_code}" if country_code else city
            return wrapper.run(query)
        except Exception as e:
            return f"Failed to fetch weather: {str(e)}"

    async def _arun(self, city: str, country_code: Optional[str] = None) -> str:
        return self._run(city, country_code)


def create_weather_tool():
    return WeatherTool()
