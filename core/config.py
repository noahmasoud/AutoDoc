from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./app.db"
    CORS_ORIGINS: list[str] = ["http://localhost:4200"]

    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")


settings = Settings()
