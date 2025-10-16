import os
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class DatabaseSettings(BaseSettings):
    # database config
    host: str = Field(default="localhost", env="DB_HOST")
    port: int = Field(default=5432, env="DB_PORT")
    database: str = Field(default="pubmed_db", env="DB_NAME")
    user: str = Field(default="postgres", env="DB_USER")
    password: str = Field(default="", env="DB_PASSWORD")
    
    @validator('port')
    def port_must_be_valid(cls, v):
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v

class GeminiSettings(BaseSettings):
    # gemini ai config
    api_key: str = Field(default=None, env="GEMINI_API")
    model_name: str = Field(default="gemini-2.0-flash", env="GEMINI_MODEL_NAME")
    
    @validator('api_key')
    def api_key_validation(cls, v):
        if v and len(v) < 10:
            raise ValueError('API key seems too short')
        return v

class PubMedSettings(BaseSettings):
    # pubmed api config
    base_url: str = Field(default="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/")
    max_articles: int = Field(default=150, env="MAX_ARTICLES")
    request_delay: float = Field(default=0.5, env="REQUEST_DELAY")
    
    @validator('max_articles')
    def max_articles_validation(cls, v):
        if v <= 0:
            raise ValueError('Max articles must be positive')
        if v > 10000:
            raise ValueError('Max articles too high (max 10000)')
        return v

class AppSettings(BaseSettings):
    # app settings
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    @validator('log_level')
    def log_level_validation(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()

class Settings:
    # main settings class
    
    def __init__(self):
        try:
            self.database = DatabaseSettings()
            self.gemini = GeminiSettings()
            self.pubmed = PubMedSettings()
            self.app = AppSettings()
        except Exception as e:
            raise ValueError(f"Configuration error: {e}")
    
    def validate_all(self):
        # check if settings are valid
        try:
            db_url = f"postgresql://{self.database.user}:{self.database.password}@{self.database.host}:{self.database.port}/{self.database.database}"
            return True
        except Exception as e:
            print(f"Settings validation failed: {e}")
            return False

settings = Settings()
