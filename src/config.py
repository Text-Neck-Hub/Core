from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = None
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES: int
    JWT_REFRESH_TOKEN_LIFETIME_DAYS: int
    JWT_USER_ID_CLAIM: str
    JWT_JTI_CLAIM: str
    JWT_AUDIENCE: str
    JWT_ISSUER: str

    CORE_DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file='/app/src/.env',
        extra='ignore'
    )


settings = Settings()
