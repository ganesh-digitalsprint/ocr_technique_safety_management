from fastapi import APIRouter, Request, HTTPException,Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.config.database import get_db
from app.services.weather_service import (
    fetch_weather_service,
    get_hourly_forecast,
    get_three_day_forecast,
    save_weather_data
)

router = APIRouter(prefix="/api/v1", tags=["Weather"])

@router.api_route("/weather", methods=["GET", "POST"])
async def weather_api(request: Request, db: Session = Depends(get_db)):
    if request.method == "GET":
        city = request.query_params.get("city")
    else:
        data = await request.json()
        city = data.get("city")

    if not city:
        raise HTTPException(status_code=400, detail="City is required")

    try:
        # Fetch current weather
        weather = fetch_weather_service(city)

        # Save to DB
        save_weather_data(db, city, weather['temperature'], weather['humidity'], weather['wind_speed'])

        # Get forecasts
        hourly = get_hourly_forecast(city)
        daily = get_three_day_forecast(city)

        return JSONResponse(content={
            'city': city,
            'current': weather,
            'hourly_forecast': hourly,
            'three_day_forecast': daily,
            'message': 'Weather data fetched and stored successfully.'
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

