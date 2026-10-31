"""Biểu đồ so sánh; mọi số liệu đều lấy từ runs.csv và các bảng gốc."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import NullFormatter, ScalarFormatter

from src.config import PATHS, load_config
from src.data.loaders import load_processed
from src.data.study_area import load_districts
from src.experiments.analyze import b1_vs_b2, bfs_report, gbfs_gap_vs_detour
from src.viz.expansion_maps import ALGO_LABELS, ROAD_COLOR, SURFACE, TEXT_SECONDARY, add_attribution, edges_projected

ALGO_COLORS = {"BFS": "#2a78d6", "GBFS": "#eb6834", "ASTAR": "#1baf7a", "UCS": "#eda100"}
ALGO_ORDER = ["BFS", "GBFS", "ASTAR", "UCS"]
GRID_COLOR = "#e4e3de"
TEXT_PRIMARY = "#0b0b0b"
NAMED_CASES = ["C1", "C2", "C3", "C3b", "C4", "C5a", "C5b", "C5c"]
# Vị trí nhãn tên quận (điểm, căn lề), để không đè lên cạnh và trọng số.
LEVEL_A_LABELS = {"HK": ((0, 11), "center"), "NTL": ((-9, -5), "right"), "HBT": ((10, -14), "left")}


def _style(ax) -> None:
    ax.set_facecolor(SURFACE)
    ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID_COLOR)
    ax.tick_params(colors=TEXT_SECONDARY, length=0)
    ax.yaxis.label.set_color(TEXT_SECONDARY)
    ax.xaxis.label.set_color(TEXT_SECONDARY)


def _save(fig, name) -> None:
    fig.tight_layout()
    fig.savefig(PATHS.FIGURES / name, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def _algo_handles():
    return [
        plt.Line2D([], [], marker="s", linestyle="", markersize=9, color=ALGO_COLORS[a], label=ALGO_LABELS[a])
        for a in ALGO_ORDER
    ]


def fig_expanded_by_case(df) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(10, 7.5), facecolor=SURFACE)
    width = 0.2
    for ax, dataset in zip(axes, ["B1", "B2"]):
        data = df[(df["dataset"] == dataset) & df["case_id"].isin(NAMED_CASES)]
        pivot = data.pivot(index="case_id", columns="algorithm", values="expanded").reindex(NAMED_CASES)
        positions = np.arange(len(NAMED_CASES))
        for i, algorithm in enumerate(ALGO_ORDER):
            ax.bar(positions + (i - 1.5) * width, pivot[algorithm], width=width, color=ALGO_COLORS[algorithm], edgecolor=SURFACE, linewidth=1)
        ax.set_yscale("log")
        ax.set_xticks(positions, NAMED_CASES)
        ax.set_ylabel("Số nút mở rộng (log)")
        ax.set_title(dataset, loc="left", fontsize=12, color=TEXT_PRIMARY)
        _style(ax)
    axes[0].legend(handles=_algo_handles(), ncols=4, frameon=False, loc="upper left", bbox_to_anchor=(0.1, 1.17))
    _save(fig, "fig_expanded_by_case.png")


def fig_expanded_vs_distance(df) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True, facecolor=SURFACE)
    data = df[df["property"].isin(["distance_scaling", "random"])]
    for ax, dataset in zip(axes, ["B1", "B2"]):
        for algorithm in ALGO_ORDER:
            group = data[(data["dataset"] == dataset) & (data["algorithm"] == algorithm)]
            ax.scatter(group["d_euclid_m"] / 1000, group["expanded"], s=26, color=ALGO_COLORS[algorithm], edgecolors=SURFACE, linewidths=0.8)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xticks([1, 2, 5, 10, 20])
        ax.xaxis.set_major_formatter(ScalarFormatter())
        ax.xaxis.set_minor_formatter(NullFormatter())
        ax.set_xlabel("Khoảng cách chim bay kho–đích (km, log)")
        ax.set_title(dataset, loc="left", fontsize=12, color=TEXT_PRIMARY)
        _style(ax)
    axes[0].set_ylabel("Số nút mở rộng (log)")
    axes[1].legend(handles=_algo_handles(), frameon=False, loc="lower right")
    _save(fig, "fig_expanded_vs_distance.png")


def fig_gbfs_gap_vs_detour(df) -> None:
    correlations = gbfs_gap_vs_detour(df).set_index("dataset")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True, facecolor=SURFACE)
    for ax, dataset in zip(axes, ["B1", "B2"]):
        group = df[(df["dataset"] == dataset) & (df["algorithm"] == "GBFS")].drop_duplicates(["source", "target"])
        ax.scatter(group["detour"], group["gap_pct"], s=30, color=ALGO_COLORS["GBFS"], edgecolors=SURFACE, linewidths=0.8)
        row = correlations.loc[dataset]
        ax.set_title(f"{dataset}: Spearman ρ = {row['spearman_rho']:.2f}, p = {row['p_value']:.3f}, n = {int(row['n'])}", loc="left", fontsize=11, color=TEXT_PRIMARY)
        ax.set_xlabel("Tỉ lệ vòng (đường bộ / chim bay)")
        _style(ax)
    axes[0].set_ylabel("Mức mất tối ưu của GBFS (%)")
    _save(fig, "fig_gbfs_gap_vs_detour.png")


def fig_bfs_hops_vs_km(df) -> None:
    report = bfs_report(df)
    labels = [f"{row.dataset}\n{row.group}" for row in report.itertuples()]
    positions = np.arange(len(report))
    width = 0.36
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), facecolor=SURFACE)
    for ax, (bfs_col, ucs_col, ylabel) in zip(axes, [("hops_bfs", "hops_ucs", "Số cạnh"), ("km_bfs", "km_ucs", "Quãng đường (km)")]):
        ax.bar(positions - width / 2, report[bfs_col], width=width, color=ALGO_COLORS["BFS"], edgecolor=SURFACE, linewidth=1, label="BFS")
        ax.bar(positions + width / 2, report[ucs_col], width=width, color=ALGO_COLORS["UCS"], edgecolor=SURFACE, linewidth=1, label="UCS (tối ưu)")
        ax.set_xticks(positions, labels, fontsize=9)
        ax.set_ylabel(ylabel)
        _style(ax)
    axes[0].legend(frameon=False)
    _save(fig, "fig_bfs_hops_vs_km.png")


def fig_b1_vs_b2(df) -> None:
    table = b1_vs_b2(df).set_index("algorithm").reindex(ALGO_ORDER)
    fig, ax = plt.subplots(figsize=(7.5, 4.8), facecolor=SURFACE)
    width = 0.2
    positions = np.arange(2)
    for i, algorithm in enumerate(ALGO_ORDER):
        values = [table.loc[algorithm, "expanded_b1_median"], table.loc[algorithm, "expanded_b2_median"]]
        bars = ax.bar(positions + (i - 1.5) * width, values, width=width, color=ALGO_COLORS[algorithm], edgecolor=SURFACE, linewidth=1)
        ax.bar_label(bars, labels=[f"{v:,.0f}" for v in values], fontsize=8, color=TEXT_SECONDARY, padding=2)
    ax.set_yscale("log")
    ax.set_xticks(positions, ["B1 (chi tiết)", "B2 (trục chính)"])
    ax.set_ylabel("Trung vị số nút mở rộng (log)")
    ax.set_title(f"{int(table['n_pairs'].iloc[0])} đích ngẫu nhiên có mặt trên cả hai đồ thị", loc="left", fontsize=11, color=TEXT_PRIMARY)
    ax.legend(handles=_algo_handles(), ncols=4, frameon=False, loc="upper right")
    ax.set_ylim(top=ax.get_ylim()[1] * 6)
    _style(ax)
    _save(fig, "fig_b1_vs_b2.png")


def fig_dataset_overview() -> None:
    stats = pd.read_csv(PATHS.TABLES / "dataset_stats.csv").set_index("dataset")
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.6), facecolor=SURFACE)
    for ax, dataset in zip(axes, ["B1", "B2"]):
        edges_projected(load_processed(dataset)).plot(ax=ax, color="#52514e", linewidth=0.25 if dataset == "B1" else 0.5)
        row = stats.loc[dataset]
        ax.set_title(f"{dataset}: {int(row['n_nodes_after']):,} nút, {int(row['n_edges_after']):,} cạnh, {row['total_km_after']:,.0f} km", fontsize=12)
        ax.set_aspect("equal")
        ax.set_axis_off()
    add_attribution(fig)
    _save(fig, "fig_dataset_overview.png")


def fig_level_a_graph() -> None:
    crs = load_config("datasets")["crs"]["projected"]
    districts = load_districts().to_crs(crs)
    points = pd.read_csv(PATHS.TABLES / "A_points.csv").set_index("id")
    edges = pd.read_csv(PATHS.TABLES / "A_edges.csv")
    edges = edges[edges["accepted"]]

    fig, ax = plt.subplots(figsize=(10, 9.5), facecolor=SURFACE)
    districts.plot(ax=ax, color="#f2f1ec", edgecolor=ROAD_COLOR, linewidth=1)
    for row in edges.itertuples(index=False):
        a, b = points.loc[row.u], points.loc[row.v]
        ax.plot([a.x, b.x], [a.y, b.y], color="#2a78d6", linewidth=2, zorder=2)
        ax.text(
            (a.x + b.x) / 2, (a.y + b.y) / 2, f"{row.weight_m / 1000:.1f}", fontsize=9, color=TEXT_PRIMARY,
            ha="center", va="center", zorder=3,
            bbox={"boxstyle": "round,pad=0.15", "facecolor": SURFACE, "edgecolor": "none"},
        )  # fmt: skip
    ax.scatter(points["x"], points["y"], s=70, color="#0b0b0b", edgecolors=SURFACE, linewidths=1.5, zorder=4)
    for row in points.itertuples():
        offset, align = LEVEL_A_LABELS.get(row.Index, ((6, 7), "left"))
        ax.annotate(row.name, (row.x, row.y), xytext=offset, textcoords="offset points", ha=align, fontsize=10, color=TEXT_PRIMARY, zorder=5)
    ax.set_title("Đồ thị A: 12 quận cũ, trọng số là quãng đường trên B2 (km)", fontsize=13)
    ax.set_aspect("equal")
    ax.set_axis_off()
    add_attribution(fig)
    _save(fig, "fig_levelA_graph.png")


def make_all_charts() -> None:
    PATHS.FIGURES.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(PATHS.TABLES / "runs.csv")
    fig_expanded_by_case(df)
    fig_expanded_vs_distance(df)
    fig_gbfs_gap_vs_detour(df)
    fig_bfs_hops_vs_km(df)
    fig_b1_vs_b2(df)
    fig_dataset_overview()
    fig_level_a_graph()
