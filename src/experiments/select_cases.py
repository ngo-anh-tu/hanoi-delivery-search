"""Biến các ca có tên thành cặp nút trên từng đồ thị, kiểm tra tiêu chí, sinh đích ngẫu nhiên."""

import math

import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point

from src.config import PATHS, load_config, update_run_metadata
from src.data.loaders import load_processed, load_search_graph
from src.data.locations import resolve_all, snap, to_projected
from src.data.study_area import districts_union, load_districts
from src.search import run, ucs_all

MIN_DETOUR_EUCLID_M = 200
GAP_EPS_M = 1e-6

CASE_COLUMNS = [
    "case_id", "property", "dataset", "depot_id", "depot_node", "target_id", "target_query",
    "target_lat", "target_lon", "target_node", "snap_dist_m", "d_euclid_m", "d_road_m",
    "detour", "bearing_deg", "check_status", "auto_replaced", "note",
]  # fmt: skip


def bearing(sg, a, b) -> float:
    """Góc phương vị 0–360° (bắc = 0, theo chiều kim đồng hồ) tính trên UTM."""
    return math.degrees(math.atan2(sg.x[b] - sg.x[a], sg.y[b] - sg.y[a])) % 360


def _angle_diff(a, b) -> float:
    return abs((a - b + 180) % 360 - 180)


def detour_table(sg, depot_node) -> pd.DataFrame:
    """Chạy ucs_all một lần; bỏ nút gần kho hơn 200 m để tránh chia cho số rất nhỏ."""
    dist = ucs_all(sg, depot_node)
    rows = []
    for node, d_road in dist.items():
        d_euclid = math.hypot(sg.x[node] - sg.x[depot_node], sg.y[node] - sg.y[depot_node])
        if d_euclid < MIN_DETOUR_EUCLID_M:
            continue
        rows.append(
            {
                "node": node,
                "lat": sg.lat[node],
                "lon": sg.lon[node],
                "d_road_m": d_road,
                "d_euclid_m": d_euclid,
                "detour": d_road / d_euclid,
                "bearing_deg": bearing(sg, depot_node, node),
            }
        )
    return pd.DataFrame(rows).set_index("node", drop=False).rename_axis(None)


def _gap_ratio(sg, source, target, algorithm, heuristic) -> float:
    """Tỉ lệ path_m / optimal_m của một thuật toán."""
    path_m = run(algorithm, sg, source, target, heuristic).cost_m
    optimal_m = run("UCS", sg, source, target).cost_m
    return path_m / optimal_m if optimal_m > 0 else 1.0


def check_case(case, sg, detour_df, cfg) -> dict:
    """Tính các chỉ số của ca và trạng thái PASS/FAIL theo mục 4.2.

    Nhóm distance_scaling được kiểm tra chung ở _fix_distance_group vì tiêu chí so giữa ba đích.
    """
    checks = cfg["checks"]
    heuristic = cfg["heuristic"]
    target = case["target_node"]
    if target not in detour_df.index:
        return {
            "d_euclid_m": math.nan, "d_road_m": math.nan, "detour": math.nan, "bearing_deg": math.nan,
            "check_status": "FAIL", "reason": f"đích cách kho dưới {MIN_DETOUR_EUCLID_M} m",
        }  # fmt: skip

    row = detour_df.loc[target]
    detour = row["detour"]
    d_euclid = row["d_euclid_m"]
    prop = case["property"]
    passed = True
    reason = ""
    if prop == "easy":
        passed = detour <= checks["easy_detour_max"]
        reason = f"detour = {detour:.2f}"
    elif prop == "good_heuristic":
        passed = detour <= checks["good_detour_max"] and d_euclid >= checks["good_min_euclid_m"]
        reason = f"detour = {detour:.2f}, d_euclid = {d_euclid:.0f} m"
    elif prop == "gbfs_trap":
        ratio = _gap_ratio(sg, case["depot_node"], target, "GBFS", heuristic)
        passed = detour >= checks["trap_detour_min"] and ratio > 1 + GAP_EPS_M
        reason = f"detour = {detour:.2f}, gap(GBFS) = {(ratio - 1) * 100:.2f}%"
    elif prop == "bfs_hop_bias":
        ratio = _gap_ratio(sg, case["depot_node"], target, "BFS", heuristic)
        passed = ratio >= checks["bfs_gap_min_ratio"]
        reason = f"km(BFS)/km(tối ưu) = {ratio:.3f}"
    return {
        "d_euclid_m": d_euclid,
        "d_road_m": row["d_road_m"],
        "detour": detour,
        "bearing_deg": row["bearing_deg"],
        "check_status": "PASS" if passed else "FAIL",
        "reason": reason,
    }


def _nearest_to(sg, candidates, node):
    """Nút trong candidates gần node nhất (Euclid UTM), phá hòa theo id."""
    x0, y0 = sg.x[node], sg.y[node]
    return min(candidates, key=lambda n: (math.hypot(sg.x[n] - x0, sg.y[n] - y0), n))


def auto_replace(case, sg, detour_df, cfg, random_nodes=()) -> int | None:
    """Áp quy tắc "Nếu không đạt" ở bảng 4.2; trả nút đích mới, hoặc None nếu không tìm ra."""
    checks = cfg["checks"]
    prop = case["property"]
    source = case["depot_node"]
    if prop == "easy":
        pool = detour_df[detour_df["detour"] <= checks["easy_detour_max"]]
        return _nearest_to(sg, pool.index, case["target_node"]) if len(pool) else None
    if prop == "good_heuristic":
        pool = detour_df[
            (detour_df["detour"] <= checks["good_detour_max"])
            & (detour_df["d_euclid_m"] >= checks["good_min_euclid_m"])
        ]
        return _nearest_to(sg, pool.index, case["target_node"]) if len(pool) else None
    if prop == "gbfs_trap":
        far = detour_df[detour_df["d_euclid_m"] >= checks["trap_auto_min_euclid_m"]]
        ranked = far.sort_values(["detour", "node"], ascending=[False, True]).head(checks["trap_auto_top_k"])
        for node in ranked.index:
            if _gap_ratio(sg, source, node, "GBFS", cfg["heuristic"]) > 1 + GAP_EPS_M:
                return node
        return None
    if prop == "bfs_hop_bias":
        ratios = {node: _gap_ratio(sg, source, node, "BFS", cfg["heuristic"]) for node in random_nodes}
        return max(ratios, key=lambda n: (ratios[n], -n)) if ratios else None
    return None


def sample_random_points(union_polygon, n, seed, depot_latlon, min_dist_m) -> pd.DataFrame:
    """Lấy mẫu loại bỏ trong polygon, cố định seed; loại điểm quá gần kho."""
    crs = load_config("datasets")["crs"]["projected"]
    transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    depot_x, depot_y = transformer.transform(depot_latlon[1], depot_latlon[0])
    west, south, east, north = union_polygon.bounds
    rng = np.random.default_rng(seed)
    rows = []
    while len(rows) < n:
        lon = rng.uniform(west, east)
        lat = rng.uniform(south, north)
        if not union_polygon.contains(Point(lon, lat)):
            continue
        x, y = transformer.transform(lon, lat)
        if math.hypot(x - depot_x, y - depot_y) < min_dist_m:
            continue
        rows.append({"point_id": f"R{len(rows) + 1:02d}", "lat": lat, "lon": lon})
    return pd.DataFrame(rows)


def _replace_row(row, node, sg, detour_df, cfg, reason, snap_note) -> dict:
    """Đổi đích của một ca sang node, kiểm tra lại và ghi chú lý do."""
    original = row["target_id"]
    row.update(
        target_id=f"AUTO_{original}",
        target_lat=sg.lat[node],
        target_lon=sg.lon[node],
        target_node=node,
        snap_dist_m=0.0,
        auto_replaced=True,
    )
    result = check_case(row, sg, detour_df, cfg)
    status_reason = result.pop("reason")
    row.update(result)
    row["note"] = "; ".join(
        part for part in (f"{original} không đạt ({reason}), thay bằng nút {node} ({status_reason})", snap_note) if part
    )
    return row


def _fix_distance_group(rows, sg, detour_df, cfg) -> None:
    """Ba đích C5 phải lệch nhau ≤ tol; đích lệch được thay bằng nút cùng hướng gần nhất."""
    group = [row for row in rows if row["property"] == "distance_scaling"]
    if len(group) < 2:
        return
    tol = cfg["checks"]["bearing_tol_deg"]
    spread = max(_angle_diff(a["bearing_deg"], b["bearing_deg"]) for a in group for b in group)
    if spread <= tol:
        for row in group:
            row["note"] = "; ".join(p for p in (f"lệch hướng tối đa {spread:.1f}°", row["note"]) if p)
        return

    # Đích xa nhất có hướng ổn định nhất nên làm mốc; mỗi đích cách mốc ≤ tol/2 thì cặp bất kỳ ≤ tol.
    reference = max(group, key=lambda row: row["d_euclid_m"])["bearing_deg"]
    aligned = detour_df[detour_df["bearing_deg"].map(lambda b: _angle_diff(b, reference) <= tol / 2)]
    for row in group:
        if _angle_diff(row["bearing_deg"], reference) > tol / 2:
            node = _nearest_to(sg, aligned.index, row["target_node"])
            reason = f"lệch hướng {_angle_diff(row['bearing_deg'], reference):.1f}° so với mốc"
            _replace_row(row, node, sg, detour_df, cfg, reason, row["note"])
    spread = max(_angle_diff(a["bearing_deg"], b["bearing_deg"]) for a in group for b in group)
    for row in group:
        row["check_status"] = "PASS" if spread <= tol else "FAIL"


def _named_row(case_id, case, dataset, points, sg, detour_df, cfg, max_snap) -> dict:
    depot = points.loc[case["depot"]]
    target = points.loc[case["target"]]
    row = {
        "case_id": case_id,
        "property": case["property"],
        "dataset": dataset,
        "depot_id": case["depot"],
        "depot_node": int(depot["node"]),
        "target_id": case["target"],
        "target_query": target["query"],
        "target_lat": target["lat"],
        "target_lon": target["lon"],
        "target_node": int(target["node"]),
        "snap_dist_m": target["snap_dist_m"],
        "auto_replaced": False,
    }
    result = check_case(row, sg, detour_df, cfg)
    row["_reason"] = result.pop("reason")
    row.update(result)
    snap_note = f"snap xa {target['snap_dist_m']:.0f} m" if target["snap_dist_m"] > max_snap else ""
    row["note"] = snap_note
    return row


def _random_rows(random_points, dataset, depot_id, points, G, sg, detour_df, max_snap, crs) -> list:
    depot_node = int(points.loc[depot_id, "node"])
    rows = []
    for point in random_points.itertuples(index=False):
        x, y = to_projected(point.lat, point.lon, crs)
        node, dist_m = snap(G, x, y)
        if dist_m > max_snap or node not in detour_df.index:
            continue
        info = detour_df.loc[node]
        rows.append(
            {
                "case_id": point.point_id,
                "property": "random",
                "dataset": dataset,
                "depot_id": depot_id,
                "depot_node": depot_node,
                "target_id": point.point_id,
                "target_query": "",
                "target_lat": point.lat,
                "target_lon": point.lon,
                "target_node": node,
                "snap_dist_m": dist_m,
                "d_euclid_m": info["d_euclid_m"],
                "d_road_m": info["d_road_m"],
                "detour": info["detour"],
                "bearing_deg": info["bearing_deg"],
                "check_status": "PASS",
                "auto_replaced": False,
                "note": "",
            }
        )
    return rows


def _select_dataset(dataset, random_points, cfg, loc_cfg, crs) -> list:
    G = load_processed(dataset)
    sg = load_search_graph(dataset)
    points = resolve_all(loc_cfg, dataset, G).set_index("point_id")
    max_snap = loc_cfg["geocoding"]["max_snap_dist_m"]

    depot_ids = sorted({case["depot"] for case in loc_cfg["cases"].values()} | {loc_cfg["random_targets"]["depot"]})
    tables = {}
    for depot_id in depot_ids:
        tables[depot_id] = detour_table(sg, int(points.loc[depot_id, "node"]))
        tables[depot_id].to_csv(PATHS.TABLES / f"detour_{dataset}_{depot_id}.csv", index=False)

    random_depot = loc_cfg["random_targets"]["depot"]
    random_rows = _random_rows(
        random_points, dataset, random_depot, points, G, sg, tables[random_depot], max_snap, crs
    )
    random_nodes = [row["target_node"] for row in random_rows]

    named = {}
    for case_id, case in loc_cfg["cases"].items():
        named[case_id] = _named_row(case_id, case, dataset, points, sg, tables[case["depot"]], cfg, max_snap)

    for case_id, case in loc_cfg["cases"].items():
        row = named[case_id]
        if row["check_status"] == "PASS":
            continue
        fallback_id = case.get("fallback")
        if fallback_id and named[fallback_id]["check_status"] == "PASS":
            backup = named[fallback_id]
            row.update({key: backup[key] for key in (
                "depot_id", "depot_node", "target_query", "target_lat", "target_lon", "target_node",
                "snap_dist_m", "d_euclid_m", "d_road_m", "detour", "bearing_deg",
            )})  # fmt: skip
            note = f"{row['target_id']} không đạt ({row['_reason']}), dùng dự phòng {fallback_id}"
            row.update(target_id=backup["target_id"], check_status="PASS", auto_replaced=True, note=note)
            continue
        depot_table = tables[row["depot_id"]]
        node = auto_replace(row, sg, depot_table, cfg, random_nodes)
        if node is None:
            row["note"] = f"không đạt ({row['_reason']}) và không tìm được nút thay thế"
            continue
        _replace_row(row, node, sg, depot_table, cfg, row["_reason"], row["note"])

    named_rows = list(named.values())
    _fix_distance_group(named_rows, sg, tables[random_depot], cfg)
    for row in named_rows:
        row.pop("_reason")
    return named_rows + random_rows


def select_all(datasets=None) -> pd.DataFrame:
    """Ghép mọi ca của các đồ thị yêu cầu vào cases.csv; dòng của đồ thị khác được giữ nguyên."""
    cfg = load_config("experiment")
    loc_cfg = load_config("locations")
    crs = load_config("datasets")["crs"]["projected"]
    datasets = datasets or cfg["datasets"]

    # Lấy mẫu một lần cho mọi đồ thị, để so sánh B1 với B2 trên cùng vị trí thực.
    random_cfg = loc_cfg["random_targets"]
    depot = loc_cfg["depots"][random_cfg["depot"]]
    union = districts_union(load_districts())
    random_points = sample_random_points(
        union, random_cfg["n"], random_cfg["seed"], depot["latlon"], random_cfg["min_euclid_from_depot_m"]
    )
    random_points.to_csv(PATHS.TABLES / "random_points.csv", index=False)

    rows = []
    for dataset in datasets:
        rows += _select_dataset(dataset, random_points, cfg, loc_cfg, crs)
    table = pd.DataFrame(rows, columns=CASE_COLUMNS)

    path = PATHS.TABLES / "cases.csv"
    if path.exists():
        old = pd.read_csv(path)
        table = pd.concat([old[~old["dataset"].isin(datasets)], table], ignore_index=True)
    table.to_csv(path, index=False)
    update_run_metadata(
        "select_cases",
        {
            "random_seed": random_cfg["seed"],
            "n_random_sampled": random_cfg["n"],
            "n_cases_by_dataset": table["dataset"].value_counts().to_dict(),
        },
    )
    return table
