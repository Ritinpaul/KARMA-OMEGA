"""
KARMA-OMEGA Configuration
========================
Central settings management using pydantic-settings.
All values sourced from environment variables / .env file.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ─── Application ──────────────────────────────────────────────────────────
    app_env: str = "development"
    app_version: str = "0.1.0"
    log_level: str = "DEBUG"

    # ─── MNEMOS API ───────────────────────────────────────────────────────────
    mnemos_host: str = "0.0.0.0"
    mnemos_port: int = 8001

    # ─── Neo4j ────────────────────────────────────────────────────────────────
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "karma_omega_secret"
    neo4j_database: str = "karmaomega"

    # ─── Pinecone ─────────────────────────────────────────────────────────────
    pinecone_api_key: str = ""
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "karma-omega-mnemos"
    embedding_dim: int = 768  # mpnet-base-v2 output dim

    # ─── Gemini ───────────────────────────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"

    # ─── HuggingFace ─────────────────────────────────────────────────────────
    hf_model_name: str = "sentence-transformers/all-mpnet-base-v2"
    hf_cache_dir: str = "./data/models/cache"

    # ─── Data Paths ───────────────────────────────────────────────────────────
    data_raw_dir: str = "./data/raw"
    data_processed_dir: str = "./data/processed"
    data_synthetic_dir: str = "./data/synthetic"

    def ensure_directories(self) -> None:
        """Create required data directories if they don't exist."""
        for path_str in [
            self.data_raw_dir,
            self.data_processed_dir,
            self.data_synthetic_dir,
            self.hf_cache_dir,
        ]:
            Path(path_str).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (singleton)."""
    settings = Settings()
    settings.ensure_directories()
    return settings
