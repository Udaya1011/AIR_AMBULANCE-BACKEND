import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb+srv://udaya1:udaya1@cluster0.ub6jv.mongodb.net/")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "MovieCloud_Airswift1")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

settings = Settings()