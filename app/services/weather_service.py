from pyowm.owm import OWM
from pyowm.utils.config import get_default_config
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.weather_model import WeatherData

# Setup OWM
config = get_default_config()
config['language'] = 'en'
owm = OWM('3b053ac9a618f1accfddf13be143101e')
mgr = owm.weather_manager()

def fetch_weather_service(city: str):
    observation = mgr.weather_at_place(city)
    weather = observation.weather
    return {
        'temperature': weather.temperature('celsius')['temp'],
        'humidity': weather.humidity,
        'wind_speed': weather.wind()['speed']
    }

def get_hourly_forecast(city: str):
    forecast = mgr.forecast_at_place(city, '3h')
    forecast_list = forecast.forecast.weathers[:5]
    return [
        {
            'time': w.reference_time('iso'),
            'temp': w.temperature('celsius')['temp']
        } for w in forecast_list
    ]

def get_three_day_forecast(city: str):
    forecast = mgr.forecast_at_place(city, '3h')
    forecast_data = forecast.forecast.weathers[:24]
    daily = {}
    for w in forecast_data:
        day = w.reference_time('date').strftime('%Y-%m-%d')
        daily.setdefault(day, []).append(w.temperature('celsius')['temp'])

    return [
        {
            'date': day,
            'avg_temp': round(sum(temps) / len(temps), 2)
        } for day, temps in list(daily.items())[:3]
    ]

# ✅ Save to database
def save_weather_data(db: Session, city: str, temperature: float, humidity: int, wind_speed: float):
    weather_record = WeatherData(
        city=city,
        temperature=temperature,
        humidity=humidity,
        wind_speed=wind_speed,
        timestamp=datetime.now()
    )
    db.add(weather_record)
    db.commit()
