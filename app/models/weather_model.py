from sqlalchemy import Column, Integer, Float, String, DateTime
from datetime import datetime
from app.config.database import Base  # ✅ Use the project's shared Base

class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String(100))
    temperature = Column(Float)
    humidity = Column(Integer)
    wind_speed = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
