"""Tải B1 và B2 từ OpenStreetMap vào data/raw."""

from datetime import datetime, timezone
from pathlib import Path

import networkx as nx
import osmnx as ox

from src.config import PATHS, load_config, update_run_metadata
from src.data.study_area import compute_bbox


def configure_osmnx(cfg) -> None:
    ox.settings.use_cache = cfg["osmnx"]["use_cache"]
    ox.settings.cache_folder = str(PATHS.ROOT / "cache")
    ox.settings.log_console = False


def build_filter(ds_cfg) -> str | None:
    """Trả custom_filter; nếu include_tertiary thì chèn tertiary vào regex của highway."""
    custom_filter = ds_cfg.get("custom_filter")
    if custom_filter and ds_cfg.get("include_tertiary"):
        return custom_filter.replace('["highway"~"', '["highway"~"tertiary|tertiary_link|', 1)
    return custom_filter


def download_dataset(name, cfg=None, force=False) -> Path:
    """Tải một đồ thị; đã có snapshot thì giữ nguyên trừ khi force=True."""
    cfg = cfg or load_config("datasets")
    configure_osmnx(cfg)
    existing = sorted(PATHS.DATA_RAW.glob(f"{name}_*.graphml"))
    if existing and not force:
        print(f"{name}: đã có {existing[-1].name}, bỏ qua (dùng --force để tải lại)")
        return existing[-1]

    now = datetime.now(timezone.utc)
    out_path = PATHS.DATA_RAW / f"{name}_{now:%Y%m%d}.graphml"
    ds_cfg = cfg["datasets"][name]
    bbox = compute_bbox(cfg)
    custom_filter = build_filter(ds_cfg)
    G = ox.graph_from_bbox(
        bbox,
        network_type=ds_cfg.get("network_type") or "all",
        custom_filter=custom_filter,
        simplify=cfg["osmnx"]["simplify"],
        retain_all=cfg["osmnx"]["retain_all"],
    )
    PATHS.DATA_RAW.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(G, out_path)

    update_run_metadata(
        f"download_{name}",
        {
            "downloaded_at_utc": now.isoformat(timespec="seconds"),
            "file": out_path.name,
            "osmnx_version": ox.__version__,
            "networkx_version": nx.__version__,
            "bbox_west_south_east_north": list(bbox),
            "network_type": ds_cfg.get("network_type"),
            "custom_filter": custom_filter,
            "n_nodes": G.number_of_nodes(),
            "n_edges": G.number_of_edges(),
        },
    )
    return out_path
