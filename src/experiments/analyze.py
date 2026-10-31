"""Biến runs.csv thành câu trả lời cho RQ1–RQ4."""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from src.config import PATHS

GAP_ZERO_PCT = 1e-6


def _unique_pairs(df) -> pd.DataFrame:
    """Bỏ các ca trùng cặp nguồn–đích (C1 với C5a, C2 với C5c) để không đếm hai lần."""
    return df.drop_duplicates(["dataset", "algorithm", "source", "target"])


def summary(df) -> pd.DataFrame:
    """Theo dataset × algorithm: expanded, tỉ lệ so với UCS, gap, % tối ưu, thời gian."""
    ucs = df[df["algorithm"] == "UCS"].set_index(["dataset", "case_id"])["expanded"]
    keys = pd.MultiIndex.from_frame(df[["dataset", "case_id"]])
    data = df.assign(
        ratio_to_ucs=df["expanded"].to_numpy() / ucs.reindex(keys).to_numpy(),
        is_optimal=df["gap_pct"].abs() < GAP_ZERO_PCT,
    )
    table = (
        data.groupby(["dataset", "algorithm"], sort=False)
        .agg(
            n_cases=("case_id", "nunique"),
            expanded_mean=("expanded", "mean"),
            expanded_median=("expanded", "median"),
            expanded_ratio_to_ucs_median=("ratio_to_ucs", "median"),
            gap_pct_median=("gap_pct", "median"),
            gap_pct_max=("gap_pct", "max"),
            optimal_pct=("is_optimal", lambda s: s.mean() * 100),
            runtime_ms_median=("runtime_ms", "median"),
        )
        .reset_index()
    )
    return table.round(3)


def summary_by_property(df) -> pd.DataFrame:
    """Bảng cho các ca có tên và nhóm ngẫu nhiên, theo tính chất."""
    table = (
        df.groupby(["dataset", "property", "algorithm"], sort=False)
        .agg(
            n_cases=("case_id", "nunique"),
            expanded_median=("expanded", "median"),
            hops_median=("hops", "median"),
            path_km_median=("path_m", lambda s: s.median() / 1000),
            gap_pct_median=("gap_pct", "median"),
            gap_pct_max=("gap_pct", "max"),
        )
        .reset_index()
    )
    return table.round(3)


def gbfs_gap_vs_detour(df) -> pd.DataFrame:
    """Hệ số Spearman giữa gap_pct của GBFS và detour (RQ2), theo từng đồ thị."""
    rows = []
    for dataset, group in _unique_pairs(df[df["algorithm"] == "GBFS"]).groupby("dataset"):
        result = spearmanr(group["detour"], group["gap_pct"])
        rows.append(
            {
                "dataset": dataset,
                "n": len(group),
                "spearman_rho": round(float(result.statistic), 3),
                "p_value": round(float(result.pvalue), 4),
            }
        )
    return pd.DataFrame(rows)


def expansion_scaling(df) -> pd.DataFrame:
    """Hồi quy log(expanded) theo log(d_euclid) cho từng thuật toán (RQ4)."""
    data = _unique_pairs(df[df["property"].isin(["distance_scaling", "random"])])
    rows = []
    for (dataset, algorithm), group in data.groupby(["dataset", "algorithm"], sort=False):
        log_d = np.log(group["d_euclid_m"].astype(float))
        log_e = np.log(group["expanded"].astype(float))
        slope, intercept = np.polyfit(log_d, log_e, 1)
        rows.append(
            {
                "dataset": dataset,
                "algorithm": algorithm,
                "n": len(group),
                "slope": round(float(slope), 3),
                "r2": round(float(np.corrcoef(log_d, log_e)[0, 1] ** 2), 3),
            }
        )
    return pd.DataFrame(rows)


def bfs_report(df) -> pd.DataFrame:
    """So sánh hops và path_m của BFS với UCS trên C4 và các đích ngẫu nhiên (RQ3)."""
    pivot = df[df["algorithm"].isin(["BFS", "UCS"])].pivot_table(
        index=["dataset", "case_id", "property"], columns="algorithm", values=["hops", "path_m"]
    )
    table = pd.DataFrame(
        {
            "hops_bfs": pivot["hops"]["BFS"],
            "hops_ucs": pivot["hops"]["UCS"],
            "km_bfs": pivot["path_m"]["BFS"] / 1000,
            "km_ucs": pivot["path_m"]["UCS"] / 1000,
        }
    ).reset_index()
    table["gap_pct"] = (table["km_bfs"] / table["km_ucs"] - 1) * 100

    rows = []
    for dataset, group in table.groupby("dataset"):
        c4 = group[group["case_id"] == "C4"]
        if not c4.empty:
            rows.append({"dataset": dataset, "group": "C4", "n": 1, **c4.iloc[0][["hops_bfs", "hops_ucs", "km_bfs", "km_ucs", "gap_pct"]].to_dict()})
        random_group = group[group["property"] == "random"]
        if not random_group.empty:
            medians = random_group[["hops_bfs", "hops_ucs", "km_bfs", "km_ucs", "gap_pct"]].median().to_dict()
            rows.append({"dataset": dataset, "group": "random (trung vị)", "n": len(random_group), **medians})
    return pd.DataFrame(rows).round(3)


def b1_vs_b2(df) -> pd.DataFrame:
    """Trung vị expanded trên B1 và B2, chỉ tính các ca có mặt ở cả hai đồ thị (RQ4)."""
    b1 = df[df["dataset"] == "B1"].set_index(["case_id", "algorithm"])
    b2 = df[df["dataset"] == "B2"].set_index(["case_id", "algorithm"])
    common = b1.index.intersection(b2.index)
    paired = pd.DataFrame(
        {
            "algorithm": common.get_level_values("algorithm"),
            "property": b1.loc[common, "property"].to_numpy(),
            "expanded_b1": b1.loc[common, "expanded"].to_numpy(),
            "expanded_b2": b2.loc[common, "expanded"].to_numpy(),
        }
    )
    paired = paired[paired["property"] == "random"]
    table = (
        paired.groupby("algorithm", sort=False)
        .agg(
            n_pairs=("expanded_b1", "size"),
            expanded_b1_median=("expanded_b1", "median"),
            expanded_b2_median=("expanded_b2", "median"),
        )
        .reset_index()
    )
    table["ratio_b1_b2"] = (table["expanded_b1_median"] / table["expanded_b2_median"]).round(2)
    return table


def to_markdown(tables) -> str:
    """Xuất {tiêu đề: DataFrame} thành các bảng markdown để dán vào báo cáo."""
    parts = []
    for title, table in tables.items():
        parts.append(f"## {title}\n")
        parts.append("| " + " | ".join(map(str, table.columns)) + " |")
        parts.append("|" + "---|" * len(table.columns))
        for row in table.itertuples(index=False):
            parts.append("| " + " | ".join(map(str, row)) + " |")
        parts.append("")
    return "\n".join(parts)


def analyze_all() -> dict:
    """Đọc runs.csv, ghi summary*.csv và report_tables.md."""
    df = pd.read_csv(PATHS.TABLES / "runs.csv")
    tables = {
        "Tổng hợp theo đồ thị và thuật toán": summary(df),
        "Tổng hợp theo tính chất ca thử": summary_by_property(df),
        "RQ2: tương quan gap(GBFS) và tỉ lệ vòng": gbfs_gap_vs_detour(df),
        "RQ3: BFS so với UCS": bfs_report(df),
        "RQ4: hệ số góc log(expanded) theo log(d_euclid)": expansion_scaling(df),
        "RQ4: B1 so với B2 trên các đích ngẫu nhiên chung": b1_vs_b2(df),
    }
    runs_a_path = PATHS.TABLES / "runs_A.csv"
    if runs_a_path.exists():
        tables["Mức A: 132 cặp quận"] = summary(pd.read_csv(runs_a_path))
    tables["Tổng hợp theo đồ thị và thuật toán"].to_csv(PATHS.TABLES / "summary.csv", index=False)
    tables["Tổng hợp theo tính chất ca thử"].to_csv(PATHS.TABLES / "summary_by_property.csv", index=False)
    (PATHS.TABLES / "report_tables.md").write_text(to_markdown(tables), encoding="utf-8")
    return tables
