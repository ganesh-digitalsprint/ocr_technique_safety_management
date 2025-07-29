# app/schemas/weather_schema.py
from pydantic import BaseModel

class WeatherRequest(BaseModel):
    city: str
