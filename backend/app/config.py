from typing import List, Union

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "https://tracking-system-for-biw-2vo8.vercel.app",
        "https://protocal.biw.salon",
        "http://localhost:3000"
    ]
    ALLOWED_ORIGIN_REGEX: str = r"https://tracking-system-for-biw.*\.vercel\.app"
    ALLOWED_HOSTS: Union[str, List[str]] = ["*"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins(self) -> List[str]:
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [x.strip() for x in self.ALLOWED_ORIGINS.split(",") if x.strip()]
        return self.ALLOWED_ORIGINS

    @property
    def trusted_hosts(self) -> List[str]:
        if isinstance(self.ALLOWED_HOSTS, str):
            return [x.strip() for x in self.ALLOWED_HOSTS.split(",") if x.strip()]
        return self.ALLOWED_HOSTS


settings = Settings()
