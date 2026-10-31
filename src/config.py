"""Một chỗ duy nhất để đọc cấu hình và biết đường dẫn của project."""

import json
from pathlib import Path
from types import SimpleNamespace

import yaml

ROOT = Path(__file__).resolve().parent.parent

PATHS = SimpleNamespace(
    ROOT=ROOT,
    CONFIG=ROOT / "config",
    DATA_RAW=ROOT / "data" / "raw",
    DATA_EXTERNAL=ROOT / "data" / "external",
    DATA_INTERIM=ROOT / "data" / "interim",
    DATA_PROCESSED=ROOT / "data" / "processed",
    TABLES=ROOT / "results" / "tables",
    TRACES=ROOT / "results" / "traces",
    MAPS=ROOT / "results" / "maps",
    FIGURES=ROOT / "results" / "figures",
    RUN_METADATA=ROOT / "results" / "run_metadata.json",
)


def load_config(name: str) -> dict:
    """Đọc config/<name>.yaml."""
    with open(PATHS.CONFIG / f"{name}.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_dirs() -> None:
    """Tạo các thư mục dữ liệu và kết quả nếu chưa có."""
    for path in (
        PATHS.DATA_RAW,
        PATHS.DATA_EXTERNAL,
        PATHS.DATA_INTERIM,
        PATHS.DATA_PROCESSED,
        PATHS.TABLES,
        PATHS.TRACES,
        PATHS.MAPS,
        PATHS.FIGURES,
    ):
        path.mkdir(parents=True, exist_ok=True)


def update_run_metadata(section: str, info: dict) -> None:
    """Gộp info vào một mục của run_metadata.json, không đụng các mục khác."""
    path = PATHS.RUN_METADATA
    text = path.read_text(encoding="utf-8").strip() if path.exists() else ""
    metadata = json.loads(text) if text else {}
    metadata.setdefault(section, {}).update(info)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
