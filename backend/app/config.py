from pydantic_settings import BaseSettings
 
class Settings(BaseSettings):
    DATABASE_URL:  str
    SECRET_KEY:    str
    INVITE_CODE:   str
    MAIL_FROM:     str   # e.g. "Book Club <you@gmail.com>"
    MAIL_USER:     str   # Your Gmail address
    MAIL_PASSWORD: str   # Gmail App Password (16 chars, no spaces)
    APP_BASE_URL:  str   # e.g. https://www.yourdomain.com
 
    class Config:
        env_file = ".env"
 
settings = Settings()
