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

    orchestration_budget: int = 20

    enable_cloud_ai: bool = False
    cloud_ai_provider: str = "openai"
    openai_api_key: str | None = None
    openai_default_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    anthropic_default_model: str = "claude-sonnet-5"
    google_api_key: str | None = None
    cloud_ai_timeout_seconds: int = 60

    enabled_scanners: str = "security_headers,reflected_input"

    # Shared-secret auth. If unset, the API runs unauthenticated (dev
    # convenience) and logs a loud warning at startup -- set this for
    # anything reachable beyond localhost.
    api_key: str | None = None


settings = Settings()
