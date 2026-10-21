"""Runtime configuration loaded from ``config.yaml``."""

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

from etl.domain.errors import ConfigError

_SYNCED_MARKERS = ("onedrive", "sharepoint")


@dataclass(frozen=True)
class AppConfig:
    source_dir: Path
    output_dir: Path
    contracts_dir: Path
    working_dir: Path


def default_working_dir() -> Path:
    """``%LOCALAPPDATA%\\FinanceETL\\data`` on Windows, a user data folder elsewhere (D-12)."""
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) if base else Path.home() / ".local" / "share"
    return root / "FinanceETL" / "data"


def validate_working_dir(path: Path) -> None:
    """Block working data inside synced folders, where locking and sync conflicts corrupt files."""
    lowered = [part.lower() for part in path.parts]
    if any(marker in part for part in lowered for marker in _SYNCED_MARKERS):
        raise ConfigError(
            f"Working folder {path} looks like a OneDrive/SharePoint synced folder. "
            "Choose a local folder (D-12)."
        )


def load_config(path: Path) -> AppConfig:
    if not path.is_file():
        raise ConfigError(f"Config file not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    base = path.parent
    try:
        source_dir = base / str(raw["source_dir"])
        output_dir = base / str(raw["output_dir"])
    except KeyError as error:
        raise ConfigError(f"Missing required config key: {error.args[0]}") from error
    contracts_dir = base / str(raw.get("contracts_dir", "contracts"))
    working_raw = raw.get("working_dir")
    working_dir = Path(str(working_raw)) if working_raw else default_working_dir()
    validate_working_dir(working_dir)
    return AppConfig(source_dir, output_dir, contracts_dir, working_dir)
