from pathlib import Path

import pytest

from etl.infrastructure.sources.local_folder import LocalFolderSource

pytestmark = pytest.mark.integration


def test_local_folder_source_lists_only_matching_files(tmp_path: Path) -> None:
    (tmp_path / "GL_2026-01.xlsx").write_bytes(b"x")
    (tmp_path / "GL_2026-02.xlsx").write_bytes(b"xx")
    (tmp_path / "notes.txt").write_text("ignore me")
    source = LocalFolderSource(tmp_path, source="gl_actuals", pattern="GL_*.xlsx")
    files = source.list_files()
    assert [f.path.name for f in files] == ["GL_2026-01.xlsx", "GL_2026-02.xlsx"]
    assert files[1].size_bytes == 2
    assert files[0].source == "gl_actuals"
