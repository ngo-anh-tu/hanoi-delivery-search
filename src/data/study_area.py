"""Vùng nghiên cứu: 12 quận nội thành cũ của Hà Nội, lấy từ GADM cấp 2."""

import math
import unicodedata

import geopandas as gpd

from src.config import PATHS, load_config

KM_PER_DEG_LAT = 111.0
KM_PER_DEG_LON = 111.0 * math.cos(math.radians(21.0))


def _normalize(name) -> str:
    """Bỏ dấu, viết thường, bỏ khoảng trắng: GADM có thể ghi "BaĐình" hoặc "Ba Dinh"."""
    text = str(name).replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return "".join(text.lower().split())


def load_districts(cfg=None, districts_cfg=None) -> gpd.GeoDataFrame:
    """Lọc 12 quận của Hà Nội; trả về các cột id, name, geometry ở EPSG:4326."""
    cfg = cfg or load_config("datasets")
    districts_cfg = districts_cfg or load_config("districts")
    gadm_path = PATHS.ROOT / cfg["study_area"]["gadm_file"]
    if not gadm_path.exists():
        raise FileNotFoundError(
            f"Không thấy {gadm_path}. Tải GADM Việt Nam cấp 2 từ gadm.org vào data/external/ "
            "và sửa gadm_file trong config/datasets.yaml."
        )

    gadm = gpd.read_file(gadm_path, layer=cfg["study_area"].get("gadm_layer")).to_crs(cfg["crs"]["geographic"])
    hanoi = gadm[gadm["NAME_1"].map(_normalize) == "hanoi"]
    by_name = {_normalize(row["NAME_2"]): row.geometry for _, row in hanoi.iterrows()}

    wanted = districts_cfg["districts"]
    missing = [d["name"] for d in wanted if _normalize(d["name"]) not in by_name]
    if missing:
        hint = ""
        if "tuliem" in by_name:
            hint = (
                " Bản GADM này còn quận \"Từ Liêm\" chưa tách: dùng bản GADM mới hơn, hoặc gộp "
                "Nam/Bắc Từ Liêm thành một nút ở mức A (ghi vào docs/limitations.md)."
            )
        raise ValueError(f"GADM thiếu các quận: {missing}.{hint}")

    rows = [{"id": d["id"], "name": d["name"], "geometry": by_name[_normalize(d["name"])]} for d in wanted]
    return gpd.GeoDataFrame(rows, geometry="geometry", crs=cfg["crs"]["geographic"])


def districts_union(gdf):
    """Vùng hợp của 12 quận."""
    return gdf.geometry.union_all()


def compute_bbox(cfg=None) -> tuple[float, float, float, float]:
    """(west, south, east, north) của vùng hợp, nới thêm buffer_km."""
    cfg = cfg or load_config("datasets")
    area = cfg["study_area"]
    if area["mode"] == "manual":
        return tuple(area["manual_bbox"])
    west, south, east, north = districts_union(load_districts(cfg)).bounds
    d_lat = area["buffer_km"] / KM_PER_DEG_LAT
    d_lon = area["buffer_km"] / KM_PER_DEG_LON
    return (west - d_lon, south - d_lat, east + d_lon, north + d_lat)
