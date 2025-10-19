from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./app.db"
    CORS_ORIGINS: list[str] = ["http://localhost:4200"]
    SECRET_KEY: str = "dev-secret-key-change-in-production-must-be-32-chars-minimum"
    JWT_SECRET_KEY: str = "dev-jwt-secret-key-must-be-32-chars-minimum"

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__", extra="allow")


settings = Settings()
