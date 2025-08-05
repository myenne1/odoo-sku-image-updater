from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ALTHEA_USERNAME: str
    ALTHEA_PASSWORD: str
    ALTHEA_LOGIN_URL: str    
    ODOO_URL: str
    ODOO_DB: str
    ODOO_USERNAME: str
    ODOO_API_KEY: str
    PAGE_LIMIT: int
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create a global config instance
settings = Settings()
