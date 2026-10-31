"""Làm sạch và chiếu đồ thị: LSCC → giữ lat/lon → chiếu UTM → kiểm tra → thống kê."""

from collections import Counter
from pathlib import Path

import osmnx as ox
import pandas as pd

from src.config import PATHS, load_config, update_run_metadata

MIN_B2_KEEP_RATIO = 0.85


def largest_scc(G):
    return ox.truncate.largest_component(G, strongly=True)


def ensure_latlon(G):
    """Lưu lat, lon của mỗi nút (bằng y, x trước khi chiếu) nếu chưa có."""
    for _, data in G.nodes(data=True):
        data.setdefault("lat", data["y"])
        data.setdefault("lon", data["x"])
    return G


def project(G, crs):
    """Sau bước này x, y là mét. Không tính lại length (giữ giá trị great-circle gốc)."""
    return ox.project_graph(G, to_crs=crs)


def _validate(G) -> None:
    for node, data in G.nodes(data=True):
        if "lat" not in data or "lon" not in data:
            raise ValueError(f"Nút {node} thiếu lat/lon")
    for u, v, data in G.edges(data=True):
        if not data.get("length", 0) > 0:
            raise ValueError(f"Cạnh {u} → {v} có length không dương: {data.get('length')}")


def graph_stats(G) -> dict:
    """Số nút, số cạnh, tổng chiều dài, số cạnh một chiều, bậc ra, phân bố tag highway."""
    highways = Counter()
    n_oneway = 0
    total_m = 0.0
    for _, _, data in G.edges(data=True):
        total_m += float(data["length"])
        n_oneway += bool(data.get("oneway", False))
        tag = data.get("highway", "unknown")
        highways.update(tag if isinstance(tag, list) else [tag])
    n_nodes = G.number_of_nodes()
    n_edges = G.number_of_edges()
    return {
        "n_nodes": n_nodes,
        "n_edges": n_edges,
        "total_km": round(total_m / 1000, 1),
        "n_oneway_edges": n_oneway,
        "mean_out_degree": round(n_edges / n_nodes, 3),
        "highway_tags": dict(highways.most_common()),
    }


def _latest_raw(name) -> Path:
    candidates = sorted(PATHS.DATA_RAW.glob(f"{name}_*.graphml"))
    if not candidates:
        raise FileNotFoundError(f"Không có data/raw/{name}_*.graphml; hãy chạy scripts/01_download.py trước")
    return candidates[-1]


def _write_stats(name, before, after) -> Path:
    """Cập nhật dòng của name trong dataset_stats.csv, giữ dòng của đồ thị khác."""
    path = PATHS.TABLES / "dataset_stats.csv"
    row = {"dataset": name}
    row.update({f"{key}_before": value for key, value in before.items()})
    row.update({f"{key}_after": value for key, value in after.items()})
    row["node_keep_ratio"] = round(after["n_nodes"] / before["n_nodes"], 4)
    table = pd.DataFrame([row])
    if path.exists():
        old = pd.read_csv(path)
        table = pd.concat([old[old["dataset"] != name], table], ignore_index=True)
    PATHS.TABLES.mkdir(parents=True, exist_ok=True)
    table.sort_values("dataset").to_csv(path, index=False)
    return path


def preprocess_dataset(name) -> Path:
    cfg = load_config("datasets")
    raw_path = _latest_raw(name)
    G_raw = ox.load_graphml(raw_path)
    before = graph_stats(G_raw)

    G = largest_scc(G_raw)
    G = ensure_latlon(G)
    G = project(G, cfg["crs"]["projected"])
    _validate(G)
    after = graph_stats(G)

    PATHS.DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    out_path = PATHS.DATA_PROCESSED / f"{name}.graphml"
    ox.save_graphml(G, out_path)
    _write_stats(name, before, after)

    keep_ratio = after["n_nodes"] / before["n_nodes"]
    if name == "B2" and keep_ratio < MIN_B2_KEEP_RATIO:
        print(
            f"CẢNH BÁO: LSCC của B2 chỉ giữ {keep_ratio:.1%} số nút (< {MIN_B2_KEEP_RATIO:.0%}). "
            "Hãy đặt include_tertiary: true trong config/datasets.yaml rồi tải lại."
        )
    update_run_metadata(
        f"preprocess_{name}",
        {"raw_file": raw_path.name, "crs": cfg["crs"]["projected"], "node_keep_ratio": round(keep_ratio, 4)},
    )
    return out_path
