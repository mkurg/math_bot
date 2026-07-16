from __future__ import annotations

from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = Field(min_length=20)
    bot_username: str = Field(min_length=3)
    admin_telegram_id: int = Field(gt=0)
    database_url: str
    default_timezone: str = "Europe/Zurich"
    default_reminder_hour: int = Field(default=17, ge=7, le=20)
    default_reminder_days: str = "DAILY"
    enabled_topic_ids: str = "times_tables"
    default_topic_id: str = "times_tables"
    app_env: str = "development"
    log_level: str = "INFO"

    @field_validator("bot_username")
    @classmethod
    def strip_at_sign(cls, value: str) -> str:
        return value.removeprefix("@")

    @field_validator("default_timezone")
    @classmethod
    def validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("unknown IANA timezone") from exc
        return value

    @field_validator("default_reminder_days")
    @classmethod
    def validate_days(cls, value: str) -> str:
        allowed = {"DAILY", "WEEKDAYS", "MWF", "OFF"}
        normalized = value.upper()
        if normalized not in allowed:
            raise ValueError(f"must be one of {sorted(allowed)}")
        return normalized

    @property
    def enabled_topics(self) -> tuple[str, ...]:
        return tuple(item.strip() for item in self.enabled_topic_ids.split(",") if item.strip())

    @model_validator(mode="after")
    def validate_topics(self) -> Settings:
        if not self.enabled_topics:
            raise ValueError("at least one topic must be enabled")
        if self.default_topic_id not in self.enabled_topics:
            raise ValueError("DEFAULT_TOPIC_ID must be enabled")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
