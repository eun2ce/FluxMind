from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    api_port: int = 8000
    mq_url: str = "kafka://localhost:9092"
    mq_topic_conversation_events: str = "conversation-events"
    mq_group_id_events_consumer: str = "fluxmind-events-consumer"
    db_url: str = "postgresql+asyncpg://fluxmind:fluxmind@localhost:5432/fluxmind"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    worker_archive_interval_seconds: int = 3600
    worker_archive_older_than_days: int = 30
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    jwt_audience: str = "localhost:8000"
    jwt_issuer: str = "localhost:8000"

    class Config:
        env_prefix = "FLUXMIND_"
        env_file = ".env"

    @property
    def mq_bootstrap_servers(self) -> str:
        if self.mq_url.startswith("kafka://"):
            return self.mq_url[len("kafka://") :]
        return self.mq_url


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
