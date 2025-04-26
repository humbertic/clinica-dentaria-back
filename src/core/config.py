from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "clinica_db"
    DB_USER: str = "admin"
    DB_PASSWORD: str = "admin123"
    
    SECRET_KEY: str = "supersegredo"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
