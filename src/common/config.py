"""VARUNA GRID — settings. Loaded from .env, never hardcoded."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore",
        protected_namespaces=("settings_",),
    )

    # ── Infrastructure ──
    database_url: str = "postgresql+psycopg2://varuna:varuna@localhost:5432/varuna"
    redis_url: str = "redis://localhost:6379/0"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "varuna"
    minio_secret_key: str = "varuna_secret"
    minio_bucket: str = "varuna"
    minio_secure: bool = False

    # ── Paths ──
    data_dir: Path = Path("data")
    forcing_dir: Path = Path("data/forcing")
    scene_dir: Path = Path("data/scenes")
    cache_dir: Path = Path("data/cache")
    output_dir: Path = Path("data/output")
    model_dir: Path = Path("models")
    netra_model_path: Path = Path("models/netra_unet.torchscript")
    chhaya_model_path: Path = Path("models/chhaya_xview3.pt")
    calibration_model_path: Path = Path("models/nyaya_isotonic.joblib")

    # ── PRATIVARTAN (Phi field) ──
    phi_n_particles: int = Field(2000, gt=0)      # per ensemble member
    phi_n_ensemble: int = Field(50, gt=0)         # M perturbed realisations
    phi_dt_seconds: float = Field(900.0, gt=0)    # 15 min
    phi_grid_nx: int = Field(200, gt=0)
    phi_grid_ny: int = Field(200, gt=0)
    phi_time_bin_hours: float = Field(1.0, gt=0)
    phi_backward_margin: float = Field(1.3, ge=1.0)   # x age_prior upper bound

    # ── NYAYA ──
    nyaya_corridor_km: float = Field(5.0, gt=0)       # latent residual corridor half-width
    nyaya_inconclusive_entropy: float = Field(0.85, gt=0)  # normalised entropy threshold
    nyaya_min_posterior_for_name: float = Field(0.35, ge=0, le=1)
    ais_window_before_hours: float = Field(48.0, gt=0)
    ais_window_after_hours: float = Field(6.0, ge=0)

    # ── NETRA ──
    netra_tile_size: int = 512
    netra_confidence_threshold: float = Field(0.5, ge=0, le=1)
    netra_wind_gate_ms: float = Field(3.0, ge=0)      # below this, look-alike likely

    # ── API ──
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    demo_mode: bool = False                            # serve cached Phi, skip compute


@lru_cache
def get_settings() -> Settings:
    return Settings()
