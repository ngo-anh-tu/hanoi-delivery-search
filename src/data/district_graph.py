"""Dựng đồ thị A (12 quận) từ GADM và B2."""

import math

import networkx as nx
import pandas as pd
from shapely.geometry import LineString, Point

from src.config import PATHS, load_config, update_run_metadata
from src.data.loaders import load_processed, to_simple_digraph
from src.data.locations import Geocoder, snap, to_projected
from src.data.study_area import load_districts
from src.search import SearchGraph, ucs

# GADM khá thô nên UBND nằm sát ranh giới vẫn được coi là ở trong quận.
UBND_TOLERANCE_DEG = 0.005


def representative_points(gdf, geocoder, G_b2, crs) -> pd.DataFrame:
    """Geocode UBND; nếu thất bại thì dùng representative_point() rồi snap vào B2.

    x, y, lat, lon là của nút B2 sau khi snap, để h và trọng số đo giữa cùng hai điểm.
    """
    districts_cfg = load_config("districts")
    use_ubnd = districts_cfg["representative_source"] == "ubnd"
    queries = {d["id"]: d["ubnd_query"] for d in districts_cfg["districts"]}
    rows = []
    for _, district in gdf.iterrows():
        point = geocoder(queries[district["id"]]) if use_ubnd else None
        source = "ubnd"
        inside = point is not None and district.geometry.buffer(UBND_TOLERANCE_DEG).contains(Point(point[1], point[0]))
        if not inside:
            fallback = district.geometry.representative_point()
            point = (fallback.y, fallback.x)
            source = "polygon"
        x, y = to_projected(point[0], point[1], crs)
        node, _ = snap(G_b2, x, y)
        data = G_b2.nodes[node]
        rows.append(
            {
                "id": district["id"],
                "name": district["name"],
                "lat": data["lat"],
                "lon": data["lon"],
                "x": data["x"],
                "y": data["y"],
                "b2_node": node,
                "source": source,
            }
        )
    return pd.DataFrame(rows)


def adjacent_pairs(gdf_utm, min_shared_m) -> list:
    """Các cặp quận có ranh giới chung dài hơn min_shared_m."""
    records = list(gdf_utm[["id", "geometry"]].itertuples(index=False))
    pairs = []
    for i, a in enumerate(records):
        for b in records[i + 1 :]:
            shared = a.geometry.boundary.intersection(b.geometry.boundary).length
            if shared > min_shared_m:
                pairs.append((a.id, b.id, shared))
    return pairs


def inside_ratio(path_nodes, G_b2, poly_union_ab) -> float:
    """Tỉ lệ chiều dài đường nằm trong hợp của hai quận; G_b2 là DiGraph đã chiếu."""
    total = 0.0
    inside = 0.0
    for u, v in zip(path_nodes, path_nodes[1:]):
        data = G_b2[u][v]
        line = data.get("geometry")
        if line is None:
            line = LineString(
                [(G_b2.nodes[u]["x"], G_b2.nodes[u]["y"]), (G_b2.nodes[v]["x"], G_b2.nodes[v]["y"])]
            )
        total += line.length
        inside += line.intersection(poly_union_ab).length
    return inside / total if total > 0 else 1.0


def _round_up(value, step):
    return math.ceil(value / step) * step


def _round_down(value, step):
    return math.floor(value / step) * step


def build_edges(points, gdf_utm, G_b2, sg_b2, edge_rules, overrides, round_up_m) -> pd.DataFrame:
    """Áp quy tắc cạnh (mục 3.3) cho mỗi cặp quận kề nhau và các cặp bị ép."""
    node_of = points.set_index("id")["b2_node"].to_dict()
    poly_of = gdf_utm.set_index("id").geometry.to_dict()
    forced = {frozenset(pair) for pair in overrides.get("force_edges") or []}
    forbidden = {frozenset(pair) for pair in overrides.get("forbid_edges") or []}

    pairs = adjacent_pairs(gdf_utm, edge_rules["min_shared_boundary_m"])
    known = {frozenset(pair[:2]) for pair in pairs}
    pairs += [(*sorted(pair), 0.0) for pair in forced if pair not in known]

    rows = []
    for u, v, shared in pairs:
        forward = ucs(sg_b2, node_of[u], node_of[v])
        backward = ucs(sg_b2, node_of[v], node_of[u])
        union = poly_of[u].union(poly_of[v])
        ratio = min(inside_ratio(forward.path, G_b2, union), inside_ratio(backward.path, G_b2, union))

        key = frozenset((u, v))
        if key in forbidden:
            accepted, reason = False, "forbid_edges"
        elif key in forced:
            accepted, reason = True, "force_edges"
        elif ratio >= edge_rules["min_inside_ratio"]:
            accepted, reason = True, "rule"
        else:
            accepted, reason = False, f"inside_ratio < {edge_rules['min_inside_ratio']}"

        mean_m = (forward.cost_m + backward.cost_m) / 2
        rows.append(
            {
                "u": u,
                "v": v,
                "shared_boundary_m": round(shared, 1),
                "d_uv_m": forward.cost_m,
                "d_vu_m": backward.cost_m,
                "inside_ratio": round(ratio, 4),
                "weight_m": _round_up(mean_m, round_up_m),
                "accepted": accepted,
                "reason": reason,
            }
        )
    return pd.DataFrame(rows)


def build_graph(points, edges) -> nx.Graph:
    """Đồ thị vô hướng; length đã làm tròn lên, length_exact là giá trị mét chính xác."""
    G = nx.Graph()
    for row in points.itertuples(index=False):
        G.add_node(row.id, name=row.name, x=row.x, y=row.y, lat=row.lat, lon=row.lon, b2_node=int(row.b2_node))
    for row in edges[edges["accepted"]].itertuples(index=False):
        G.add_edge(row.u, row.v, length=float(row.weight_m), length_exact=(row.d_uv_m + row.d_vu_m) / 2)
    return G


def heuristic_matrix(points, round_down_m) -> pd.DataFrame:
    """Ma trận Euclid 12 × 12, làm tròn xuống."""
    ids = points["id"].tolist()
    xy = points.set_index("id")[["x", "y"]]
    data = [
        [_round_down(math.hypot(xy.x[a] - xy.x[b], xy.y[a] - xy.y[b]), round_down_m) for b in ids]
        for a in ids
    ]
    return pd.DataFrame(data, index=pd.Index(ids, name="id"), columns=ids)


def _validate(G, matrix) -> None:
    for u, v, data in G.edges(data=True):
        if data["length"] < matrix.loc[u, v]:
            raise ValueError(f"Cạnh {u}–{v}: weight {data['length']} < h {matrix.loc[u, v]}")
    if not nx.is_connected(G):
        components = [sorted(c) for c in nx.connected_components(G)]
        raise ValueError(
            f"Đồ thị A không liên thông: {components}. Xem results/tables/A_edges.csv "
            "rồi thêm force_edges trong config/districts.yaml."
        )


def build_district_graph() -> nx.Graph:
    """Chạy cả chuỗi và ghi A.graphml, A_edges.csv, A_points.csv, A_heuristic_matrix.csv."""
    datasets_cfg = load_config("datasets")
    districts_cfg = load_config("districts")
    level_a = load_config("experiment")["level_A"]
    crs = datasets_cfg["crs"]["projected"]

    gdf = load_districts(datasets_cfg, districts_cfg)
    gdf_utm = gdf.to_crs(crs)
    G_b2_multi = load_processed("B2")
    G_b2 = to_simple_digraph(G_b2_multi)
    sg_b2 = SearchGraph.from_networkx(G_b2)

    points = representative_points(gdf, Geocoder(), G_b2_multi, crs)
    edges = build_edges(
        points, gdf_utm, G_b2, sg_b2, districts_cfg["edge_rules"], districts_cfg["overrides"], level_a["weight_round_up_m"]
    )
    matrix = heuristic_matrix(points, level_a["heuristic_round_down_m"])

    points.to_csv(PATHS.TABLES / "A_points.csv", index=False)
    edges.to_csv(PATHS.TABLES / "A_edges.csv", index=False)
    matrix.to_csv(PATHS.TABLES / "A_heuristic_matrix.csv")

    G = build_graph(points, edges)
    _validate(G, matrix)
    nx.write_graphml(G, PATHS.DATA_PROCESSED / "A.graphml")
    update_run_metadata(
        "district_graph",
        {
            "n_nodes": G.number_of_nodes(),
            "n_edges": G.number_of_edges(),
            "point_sources": points["source"].value_counts().to_dict(),
        },
    )
    return G
