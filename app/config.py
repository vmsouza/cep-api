from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "CEP API"
    app_version: str = "1.0.0"
    debug: bool = False

    db_host: str = "localhost"
    db_port: int = 5432
    db_database: str = "cardapiosescolares"
    db_username: str = "cardapiosescolares"
    db_password: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_database}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_database}"
        )

    model_config = {"env_prefix": "", "env_file": ".env", "extra": "ignore"}


settings = Settings()
