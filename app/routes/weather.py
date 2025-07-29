from fastapi import APIRouter, Request, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.weather_service import (
    fetch_weather_service,
    get_hourly_forecast,
    get_three_day_forecast,
    save_weather_data
)

router = APIRouter(prefix="/api/v1", tags=["Weather"])

@router.get("/weather")
async def get_weather(city: str, db: Session = Depends(get_db)):
    try:
        weather = fetch_weather_service(city)
        save_weather_data(db, city, weather['temperature'], weather['humidity'], weather['wind_speed'])
        hourly = get_hourly_forecast(city)
        daily = get_three_day_forecast(city)

        return {
            'city': city,
            'current': weather,
            'hourly_forecast': hourly,
            'three_day_forecast': daily,
            'message': 'Weather data fetched and stored successfully.'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weather")
async def post_weather(data: dict = Body(...), db: Session = Depends(get_db)):
    city = data.get("city")
    if not city:
        raise HTTPException(status_code=400, detail="City is required")

    try:
        weather = fetch_weather_service(city)
        save_weather_data(db, city, weather['temperature'], weather['humidity'], weather['wind_speed'])
        hourly = get_hourly_forecast(city)
        daily = get_three_day_forecast(city)

        return {
            'city': city,
            'current': weather,
            'hourly_forecast': hourly,
            'three_day_forecast': daily,
            'message': 'Weather data fetched and stored successfully.'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
