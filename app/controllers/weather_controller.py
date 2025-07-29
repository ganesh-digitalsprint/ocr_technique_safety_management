from app.services.weather_service import fetch_weather_data
from app.schemas.weather_schema import WeatherRequest

async def get_weather(request: WeatherRequest):
    return await fetch_weather_data(request.city_name)