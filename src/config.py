from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Keys
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    FAL_API_KEY: str = "833c852c-28ae-40db-9e73-2beebcf188e3:8ce613c0ef121ecebdf51f0ee25e3f07"
    
    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    
    # Cloudinary
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    
    # Meta / Instagram
    META_ACCESS_TOKEN: str = ""
    META_INSTAGRAM_USER_ID: str = ""
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    
    # Services & Config
    PUPPETEER_SERVICE_URL: str = "http://localhost:3001"
    POSTS_PER_DAY: int = 4
    MIN_QUEUE_APPROVED: int = 10
    REVIEW_TIMEOUT_HOURS: int = 4

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
