from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SECRET_KEY: str = None
    JWT_ALGORITHM: str
    JWT_USER_ID_CLAIM: str
    JWT_JTI_CLAIM: str
    JWT_AUDIENCE: str
    JWT_ISSUER: str
    DATABASE_URL: str

    model_config = SettingsConfigDict(
        env_file=None,
        extra='ignore'
    )


settings = Settings()
