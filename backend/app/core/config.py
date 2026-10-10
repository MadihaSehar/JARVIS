from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "J.A.R.V.I.S."
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8001

    database_url: str = "sqlite:///./jarvis.db"

    ollama_base_url: str = "http://localhost:11434"
    ollama_default_model: str = "llama3.2:3b"
    ollama_timeout_seconds: int = 120

    enable_cloud_ai: bool = False
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None


settings = Settings()
