from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Resume Platform Backend"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "default_secret_key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    GCP_PROJECT_ID: str
    GEMINI_API_KEY: str
    TEMPLATES_BUCKET: str = "resume-templates-bucket"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
