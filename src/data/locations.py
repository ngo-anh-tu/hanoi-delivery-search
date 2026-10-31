"""Biến địa danh thành nút trên đồ thị: geocode (có cache) → chiếu → snap."""

import json

import osmnx as ox
import pandas as pd
from geopy.exc import GeopyError
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from pyproj import Transformer

from src.config import PATHS, load_config
from src.data.loaders import load_processed


class Geocoder:
    """Nominatim với giới hạn tốc độ và cache JSON {query: [lat, lon]}."""

    def __init__(self, cfg=None):
        cfg = cfg or load_config("locations")
        geo = cfg["geocoding"]
        self.user_agent = geo["user_agent"]
        self.min_delay = geo["min_delay_seconds"]
        self.cache_path = PATHS.ROOT / geo["cache_file"]
        text = self.cache_path.read_text(encoding="utf-8").strip() if self.cache_path.exists() else ""
        self.cache = json.loads(text) if text else {}
        self._limited = None

    def __call__(self, query):
        """Trả [lat, lon], hoặc None nếu Nominatim trả lời là không tìm ra.

        Lỗi mạng không được cache: nó không có nghĩa là địa danh không tồn tại.
        """
        if query in self.cache:
            return self.cache[query]
        if self._limited is None:
            client = Nominatim(user_agent=self.user_agent, timeout=20)
            self._limited = RateLimiter(client.geocode, min_delay_seconds=self.min_delay, swallow_exceptions=False)
        try:
            location = self._limited(query)
        except GeopyError as exc:
            raise RuntimeError(
                f"Không gọi được Nominatim cho \"{query}\" ({type(exc).__name__}). "
                "Kiểm tra mạng/DNS, hoặc điền tay latlon: [lat, lon] trong config."
            ) from exc
        self.cache[query] = [location.latitude, location.longitude] if location else None
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return self.cache[query]


def resolve_point(entry, geocoder) -> tuple[float, float]:
    """Ưu tiên latlon điền tay; nếu không có thì geocode."""
    if entry.get("latlon"):
        return tuple(entry["latlon"])
    point = geocoder(entry["query"])
    if point is None:
        raise ValueError(
            f"Nominatim không tìm ra \"{entry['query']}\". Hãy điền tay latlon: [lat, lon] "
            "trong config/locations.yaml (copy từ Google Maps)."
        )
    return tuple(point)


def to_projected(lat, lon, crs) -> tuple[float, float]:
    """Chú ý thứ tự: always_xy=True nhận (lon, lat)."""
    return Transformer.from_crs("EPSG:4326", crs, always_xy=True).transform(lon, lat)


def snap(G_proj, x, y, max_snap_dist_m=None, label="") -> tuple[int, float]:
    """Nút gần nhất trên đồ thị đã chiếu; cảnh báo nếu xa hơn max_snap_dist_m."""
    node, dist_m = ox.distance.nearest_nodes(G_proj, X=x, Y=y, return_dist=True)
    if max_snap_dist_m is not None and dist_m > max_snap_dist_m:
        print(f"CẢNH BÁO: {label} snap xa {dist_m:.0f} m (> {max_snap_dist_m} m)")
    return int(node), float(dist_m)


def resolve_all(cfg=None, dataset="B1", G_proj=None) -> pd.DataFrame:
    """Mọi kho và đích, snap vào đồ thị dataset."""
    cfg = cfg or load_config("locations")
    crs = load_config("datasets")["crs"]["projected"]
    G_proj = G_proj if G_proj is not None else load_processed(dataset)
    geocoder = Geocoder(cfg)
    max_snap = cfg["geocoding"]["max_snap_dist_m"]

    rows = []
    for point_id, entry in {**cfg["depots"], **cfg["targets"]}.items():
        lat, lon = resolve_point(entry, geocoder)
        x, y = to_projected(lat, lon, crs)
        node, dist_m = snap(G_proj, x, y, max_snap, f"{dataset}/{point_id}")
        rows.append(
            {
                "point_id": point_id,
                "query": entry["query"],
                "lat": lat,
                "lon": lon,
                "x": x,
                "y": y,
                "node": node,
                "snap_dist_m": dist_m,
            }
        )
    return pd.DataFrame(rows)
