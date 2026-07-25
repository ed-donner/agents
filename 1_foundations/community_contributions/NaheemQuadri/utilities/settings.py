from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_base_url: str = ""
    ollama_base_url: str = ""

    hf_token: str = ""
    hf_base_url: str = ""

    pushover_user_key: str = ""
    pushover_app_token: str = ""
    pushover_url: str = "https://api.pushover.net/1/messages.json"

    mailgun_api_key: str = ""
    mailgun_domain: str = ""
    mailgun_from_email: str = ""
    mailgun_recipient: str = ""

    cal_username: str = ""
    cal_slot_url: str = ""
    cal_api_key: str = ""
    cal_api_version: str = ""
