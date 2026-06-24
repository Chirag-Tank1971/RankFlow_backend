from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = ""
    supabase_db_password: str = ""
    port: int = 8000
    max_transaction_amount: float = 1_000_000.0
    app_env: str = "development"

    @property
    def resolved_database_url(self) -> str:
        url = self.database_url
        if not url:
            if self.supabase_db_password:
                raise ValueError(
                    "DATABASE_URL must be set. SUPABASE_DB_PASSWORD alone is not enough "
                    "without a full connection string template."
                )
            return "sqlite:///./test.db"

        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url


settings = Settings()
