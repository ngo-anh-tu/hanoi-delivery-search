"""Bản đồ nút mở rộng và đường đi: HTML tương tác (folium) và PNG cho báo cáo."""

import json
from functools import lru_cache

import folium
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox

from src.config import PATHS

ALGO_LABELS = {"BFS": "BFS", "GBFS": "GBFS", "ASTAR": "A*", "UCS": "UCS"}
PANEL_ALGOS = ["BFS", "GBFS", "ASTAR"]
ROUTE_COLOR = "#d62728"
SURFACE = "#fcfcfb"
ROAD_COLOR = "#d9d8d3"
TEXT_SECONDARY = "#52514e"
ATTRIBUTION = "© OpenStreetMap contributors"
# Nền xám nhạt không cần API key; dữ liệu đường và nút vẽ đè lên vẫn là của OSM.
BASEMAP_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
BASEMAP_ATTR = f"{ATTRIBUTION} | Nền: Esri, HERE, Garmin"
# Từ vàng nhạt đến vàng đậm: nút mở rộng càng muộn màu càng đậm.
EXPANSION_BINS = ["#fde9a8", "#fbd872", "#f6c343", "#eda100", "#c98500"]


@lru_cache(maxsize=4)
def edges_4326(G):
    """Cạnh của G ở EPSG:4326: {(u, v): LineString} (cạnh song song giữ cạnh ngắn nhất)."""
    edges = ox.convert.graph_to_gdfs(G, nodes=False).to_crs(4326).sort_values("length", ascending=False)
    # Cạnh ngắn nhất nằm cuối nên ghi đè các cạnh song song dài hơn.
    return {(u, v): line for (u, v, _), line in edges.geometry.items()}


@lru_cache(maxsize=4)
def edges_projected(G):
    """Toàn bộ cạnh trên CRS mét, dùng làm nền cho hình tĩnh."""
    return ox.convert.graph_to_gdfs(G, nodes=False)


def base_map(location, zoom_start, prefer_canvas=True) -> folium.Map:
    m = folium.Map(location=location, zoom_start=zoom_start, tiles=None, prefer_canvas=prefer_canvas)
    folium.TileLayer(BASEMAP_URL, attr=BASEMAP_ATTR, name="Nền bản đồ", control=False).add_to(m)
    return m


def add_attribution(fig) -> None:
    fig.text(0.995, 0.005, ATTRIBUTION, ha="right", va="bottom", fontsize=7, color=TEXT_SECONDARY)


def path_latlon(G, path) -> list:
    """Đường đi theo hình dạng thật của cạnh, dạng [[lat, lon], ...] cho folium."""
    lookup = edges_4326(G)
    points = []
    for u, v in zip(path, path[1:]):
        points += [[lat, lon] for lon, lat in lookup[(u, v)].coords]
    return points


def add_points_layer(parent, lonlat, color, radius=2) -> None:
    """Một lớp GeoJSON điểm thay vì từng marker, để vẽ được hàng chục nghìn nút."""
    feature = {
        "type": "Feature",
        "properties": {},
        "geometry": {"type": "MultiPoint", "coordinates": [[round(lon, 5), round(lat, 5)] for lon, lat in lonlat]},
    }
    folium.GeoJson(
        feature,
        marker=folium.CircleMarker(radius=radius, weight=0, fill=True, fill_opacity=0.8),
        style_function=lambda _, c=color: {"color": c, "fillColor": c, "weight": 0, "fillOpacity": 0.8},
    ).add_to(parent)


def load_traces(dataset, case_id, algorithms=("BFS", "GBFS", "ASTAR", "UCS")) -> dict:
    traces = {}
    for algorithm in algorithms:
        path = PATHS.TRACES / f"{dataset}_{case_id}_{algorithm}.json"
        if path.exists():
            traces[algorithm] = json.loads(path.read_text(encoding="utf-8"))
    return traces


def expansion_map_html(G, traces, case_row) -> folium.Map:
    """Mỗi thuật toán một FeatureGroup: nút mở rộng màu vàng, đường đi màu đỏ."""
    source = G.nodes[int(case_row["depot_node"])]
    target = G.nodes[int(case_row["target_node"])]
    center = [(source["lat"] + target["lat"]) / 2, (source["lon"] + target["lon"]) / 2]
    m = base_map(center, 13)

    for index, (algorithm, trace) in enumerate(traces.items()):
        group = folium.FeatureGroup(name=ALGO_LABELS[algorithm], show=index == 0)
        order = trace["expanded_order"]
        for chunk, color in zip(np.array_split(np.array(order), len(EXPANSION_BINS)), EXPANSION_BINS):
            if len(chunk):
                lonlat = [(G.nodes[int(n)]["lon"], G.nodes[int(n)]["lat"]) for n in chunk]
                add_points_layer(group, lonlat, color)
        folium.PolyLine(
            path_latlon(G, trace["path"]),
            color=ROUTE_COLOR,
            weight=4,
            tooltip=f"{ALGO_LABELS[algorithm]}: {len(order)} nút mở rộng",
        ).add_to(group)
        group.add_to(m)

    folium.Marker([source["lat"], source["lon"]], tooltip=f"Kho {case_row['depot_id']}", icon=folium.Icon(color="blue")).add_to(m)
    folium.Marker([target["lat"], target["lon"]], tooltip=f"Đích {case_row['target_id']}", icon=folium.Icon(color="red")).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def expansion_panels_png(G, traces, case_row, out_path) -> None:
    """1 × 3 ô (BFS, GBFS, A*), cùng khung nhìn, nền là mạng đường màu xám nhạt."""
    edges = edges_projected(G)
    source = int(case_row["depot_node"])
    target = int(case_row["target_node"])

    used = [n for algo in PANEL_ALGOS for n in traces[algo]["expanded_order"]]
    xs = np.array([G.nodes[n]["x"] for n in used])
    ys = np.array([G.nodes[n]["y"] for n in used])
    pad = 0.05 * max(np.ptp(xs), np.ptp(ys), 500)
    xlim = (xs.min() - pad, xs.max() + pad)
    ylim = (ys.min() - pad, ys.max() + pad)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5.4), facecolor=SURFACE)
    for ax, algorithm in zip(axes, PANEL_ALGOS):
        ax.set_facecolor(SURFACE)
        edges.plot(ax=ax, color=ROAD_COLOR, linewidth=0.3, zorder=1)
        order = traces[algorithm]["expanded_order"]
        ax.scatter(
            [G.nodes[n]["x"] for n in order],
            [G.nodes[n]["y"] for n in order],
            c=np.linspace(0, 1, len(order)),
            cmap=matplotlib.colors.LinearSegmentedColormap.from_list("expansion", EXPANSION_BINS),
            s=4,
            linewidths=0,
            zorder=2,
        )
        path = traces[algorithm]["path"]
        ax.plot([G.nodes[n]["x"] for n in path], [G.nodes[n]["y"] for n in path], color=ROUTE_COLOR, linewidth=1.8, zorder=3)
        ax.scatter(G.nodes[source]["x"], G.nodes[source]["y"], s=70, c="#2a78d6", edgecolors=SURFACE, linewidths=1.5, zorder=4)
        ax.scatter(G.nodes[target]["x"], G.nodes[target]["y"], s=70, c=ROUTE_COLOR, marker="s", edgecolors=SURFACE, linewidths=1.5, zorder=4)
        length_km = sum(G[u][v][min(G[u][v], key=lambda k: G[u][v][k]["length"])]["length"] for u, v in zip(path, path[1:])) / 1000
        ax.set_title(f"{ALGO_LABELS[algorithm]}: {len(order):,} nút mở rộng, {length_km:.2f} km", fontsize=11)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_aspect("equal")
        ax.set_axis_off()
    fig.suptitle(f"{case_row['dataset']} · {case_row['case_id']}: {case_row['depot_id']} → {case_row['target_id']}", fontsize=13)
    add_attribution(fig)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, facecolor=SURFACE)
    plt.close(fig)
