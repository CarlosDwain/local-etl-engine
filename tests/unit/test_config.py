from pathlib import Path

import pytest

from etl.config import load_config, validate_working_dir
from etl.domain.errors import ConfigError


def test_load_config_resolves_paths_relative_to_config(tmp_path: Path) -> None:
    (tmp_path / "config.yaml").write_text(
        "source_dir: landing\noutput_dir: out\nworking_dir: " + str(tmp_path / "work") + "\n"
    )
    config = load_config(tmp_path / "config.yaml")
    assert config.source_dir == tmp_path / "landing"
    assert config.output_dir == tmp_path / "out"
    assert config.contracts_dir == tmp_path / "contracts"


def test_load_config_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        load_config(tmp_path / "nope.yaml")


def test_load_config_missing_key_raises(tmp_path: Path) -> None:
    (tmp_path / "config.yaml").write_text("source_dir: landing\n")
    with pytest.raises(ConfigError):
        load_config(tmp_path / "config.yaml")


@pytest.mark.parametrize(
    "path", ["C:/Users/me/OneDrive - Client/work", "C:/Users/me/SharePoint/site/work"]
)
def test_working_dir_inside_synced_folder_is_rejected(path: str) -> None:
    with pytest.raises(ConfigError):
        validate_working_dir(Path(path))


def test_working_dir_local_is_accepted() -> None:
    validate_working_dir(Path("C:/Users/me/AppData/Local/FinanceETL/data"))
