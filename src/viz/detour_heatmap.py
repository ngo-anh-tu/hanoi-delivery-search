"""Bản đồ tỉ lệ vòng: tô màu mỗi nút theo detour, đánh dấu kho và các cầu."""

import folium
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.viz.expansion_maps import ROAD_COLOR, SURFACE, add_attribution, add_points_layer, base_map, edges_projected

DETOUR_MIN = 1.0
DETOUR_MAX = 2.5
# Một tông xanh, từ nhạt đến đậm: càng phải đi vòng màu càng đậm.
DETOUR_BINS = ["#c4dcf4", "#94c0ec", "#609fe0", "#2a78d6", "#1a5aa8", "#0f3d78"]
BRIDGE_COLOR = "#0b0b0b"


def _bridges(G):
    edges = edges_projected(G)
    if "bridge" not in edges.columns:
        return edges.iloc[0:0]
    return edges[edges["bridge"].notna() & (edges["bridge"] != "no")]


def detour_map(detour_df, G, depot_node) -> folium.Map:
    """Bản đồ HTML; detour được cắt trong khoảng 1,0–2,5."""
    depot = G.nodes[int(depot_node)]
    m = base_map([depot["lat"], depot["lon"]], 12)

    edges = np.linspace(DETOUR_MIN, DETOUR_MAX, len(DETOUR_BINS) + 1)
    clipped = detour_df["detour"].clip(DETOUR_MIN, DETOUR_MAX)
    bins = np.minimum(np.digitize(clipped, edges) - 1, len(DETOUR_BINS) - 1)
    for index, color in enumerate(DETOUR_BINS):
        chunk = detour_df[bins == index]
        if len(chunk):
            label = f"detour {edges[index]:.2f}–{edges[index + 1]:.2f}"
            group = folium.FeatureGroup(name=label)
            add_points_layer(group, list(zip(chunk["lon"], chunk["lat"])), color)
            group.add_to(m)

    bridges = _bridges(G)
    if len(bridges):
        group = folium.FeatureGroup(name="Cầu (tag bridge)")
        folium.GeoJson(
            bridges[["geometry"]].to_crs(4326).reset_index(drop=True).to_json(),
            style_function=lambda _: {"color": BRIDGE_COLOR, "weight": 3},
        ).add_to(group)
        group.add_to(m)

    folium.Marker([depot["lat"], depot["lon"]], tooltip="Kho", icon=folium.Icon(color="red")).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


def detour_png(detour_df, G, depot_node, title, out_path) -> None:
    edges = edges_projected(G)
    data = detour_df.sort_values("detour")
    xs = [G.nodes[n]["x"] for n in data["node"]]
    ys = [G.nodes[n]["y"] for n in data["node"]]

    fig, ax = plt.subplots(figsize=(9, 8.5), facecolor=SURFACE)
    ax.set_facecolor(SURFACE)
    edges.plot(ax=ax, color=ROAD_COLOR, linewidth=0.3, zorder=1)
    points = ax.scatter(
        xs, ys, c=data["detour"], cmap=matplotlib.colors.ListedColormap(DETOUR_BINS),
        vmin=DETOUR_MIN, vmax=DETOUR_MAX, s=5, linewidths=0, zorder=2,
    )  # fmt: skip
    bridges = _bridges(G)
    if len(bridges):
        bridges.plot(ax=ax, color=BRIDGE_COLOR, linewidth=1.2, zorder=3, label="Cầu (tag bridge)")
    depot = G.nodes[int(depot_node)]
    ax.scatter(depot["x"], depot["y"], s=110, c="#d62728", marker="s", edgecolors=SURFACE, linewidths=1.5, zorder=4, label="Kho")
    fig.colorbar(points, ax=ax, shrink=0.7, label="Tỉ lệ vòng (đường bộ / chim bay)", extend="max")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.0), ncols=2, frameon=False)
    ax.set_title(title, fontsize=13)
    ax.set_aspect("equal")
    ax.set_axis_off()
    add_attribution(fig)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, facecolor=SURFACE)
    plt.close(fig)
