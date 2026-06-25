from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    jwt_secret: str
    jwt_expires_minutes: int = 60
    seed_admin_email: str
    seed_admin_password: str
    seed_admin_nome: str = "Administrador"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
