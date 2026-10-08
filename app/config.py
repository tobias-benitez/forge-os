import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "forgeos_secret_2026")
    WHATSAPP_ACCESS_TOKEN: str = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
    PHONE_NUMBER_ID: str = os.getenv("PHONE_NUMBER_ID", "1290460274160764")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

settings = Settings()

# Compatibilidad directa
WHATSAPP_VERIFY_TOKEN = settings.WHATSAPP_VERIFY_TOKEN
WHATSAPP_ACCESS_TOKEN = settings.WHATSAPP_ACCESS_TOKEN
PHONE_NUMBER_ID = settings.PHONE_NUMBER_ID
GEMINI_API_KEY = settings.GEMINI_API_KEY