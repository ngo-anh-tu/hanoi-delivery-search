"""Chạy toàn bộ thí nghiệm: thuật toán × ca × đồ thị."""

import json
import math

import networkx as nx
import pandas as pd

from src.config import PATHS, load_config, update_run_metadata
from src.data.loaders import load_heuristic_matrix, load_processed, load_search_graph, to_simple_digraph
from src.search import run
from src.search.common import timed_run
from src.search.heuristics import from_matrix

RUN_COLUMNS = [
    "dataset", "case_id", "property", "algorithm", "source", "target", "found", "expanded", "generated",
    "stale_skipped", "reopened", "max_frontier", "hops", "path_m", "optimal_m", "gap_pct", "runtime_ms",
    "d_euclid_m", "detour",
]  # fmt: skip


def _write_trace(row, algorithm, result) -> None:
    trace = {"path": result.path, "expanded_order": result.expanded_order}
    if result.steps is not None:
        trace["steps"] = result.steps
    PATHS.TRACES.mkdir(parents=True, exist_ok=True)
    path = PATHS.TRACES / f"{row['dataset']}_{row['case_id']}_{algorithm}.json"
    path.write_text(json.dumps(trace, ensure_ascii=False) + "\n", encoding="utf-8")


def run_case(sg, row, algorithms, heuristic, timing_cfg, save_trace="none") -> list:
    """Chạy mọi thuật toán trên một ca; save_trace là "none", "order" hoặc "steps"."""
    source, target = row["source"], row["target"]
    records = []
    for algorithm in algorithms:
        result, median_ms = timed_run(
            run, algorithm, sg, source, target, heuristic,
            warmup=timing_cfg["warmup"], repeats=timing_cfg["repeats"],
        )  # fmt: skip
        if save_trace != "none":
            _write_trace(row, algorithm, run(algorithm, sg, source, target, heuristic, trace_level=save_trace))
        records.append(
            {
                "dataset": row["dataset"],
                "case_id": row["case_id"],
                "property": row["property"],
                "algorithm": algorithm,
                "source": source,
                "target": target,
                "found": result.found,
                "expanded": result.expanded,
                "generated": result.generated,
                "stale_skipped": result.stale_skipped,
                "reopened": result.reopened,
                "max_frontier": result.max_frontier,
                "hops": result.hops,
                "path_m": result.cost_m,
                "runtime_ms": median_ms,
                "d_euclid_m": row["d_euclid_m"],
                "detour": row["detour"],
            }
        )

    optimal_m = next((r["path_m"] for r in records if r["algorithm"] == "UCS"), None)
    if optimal_m is None:
        optimal_m = run("UCS", sg, source, target).cost_m
    for record in records:
        record["optimal_m"] = optimal_m
        record["gap_pct"] = (record["path_m"] / optimal_m - 1) * 100 if optimal_m > 0 else 0.0
    return records


def run_dataset(name, save_traces=True) -> pd.DataFrame:
    """Chạy mọi ca của một đồ thị (có tên + R01–R50), kèm sanity_checks."""
    cfg = load_config("experiment")
    cases = pd.read_csv(PATHS.TABLES / "cases.csv", keep_default_na=False)
    cases = cases[cases["dataset"] == name]
    if cases.empty:
        raise ValueError(f"cases.csv không có ca nào của {name}; hãy chạy scripts/04_select_cases.py trước")

    sg = load_search_graph(name)
    save_for = cfg["traces"]["save_for"] if save_traces else "none"
    records = []
    for case in cases.to_dict("records"):
        row = {
            "dataset": name,
            "case_id": case["case_id"],
            "property": case["property"],
            "source": int(case["depot_node"]),
            "target": int(case["target_node"]),
            "d_euclid_m": float(case["d_euclid_m"]),
            "detour": float(case["detour"]),
        }
        is_named = case["property"] != "random"
        wants_trace = save_for == "all" or (save_for == "named_cases" and is_named)
        records += run_case(sg, row, cfg["algorithms"], cfg["heuristic"], cfg["timing"], "order" if wants_trace else "none")

    df = pd.DataFrame(records, columns=RUN_COLUMNS)
    sanity_checks(df)
    update_run_metadata(f"benchmark_{name}", {"heuristic": cfg["heuristic"], "n_runs": len(df), "seed": cfg["seed"]})
    return df


def run_level_A(save_traces=True) -> pd.DataFrame:
    """132 cặp × 4 thuật toán; các cặp để chạy tay được lưu thêm trace mức steps."""
    cfg = load_config("experiment")
    sg = load_search_graph("A")
    matrix = load_heuristic_matrix()
    heuristic = lambda graph, target: from_matrix(matrix, target)  # noqa: E731
    candidates = {tuple(pair) for pair in cfg["level_A"]["hand_trace_candidates"]}

    records = []
    for source in sorted(sg.adj):
        for target in sorted(sg.adj):
            if source == target:
                continue
            d_euclid = math.hypot(sg.x[source] - sg.x[target], sg.y[source] - sg.y[target])
            optimal_m = run("UCS", sg, source, target).cost_m
            row = {
                "dataset": "A",
                "case_id": f"{source}-{target}",
                "property": "level_A",
                "source": source,
                "target": target,
                "d_euclid_m": d_euclid,
                "detour": optimal_m / d_euclid,
            }
            wants_trace = save_traces and (source, target) in candidates
            records += run_case(sg, row, cfg["algorithms"], heuristic, cfg["timing"], "steps" if wants_trace else "none")

    df = pd.DataFrame(records, columns=RUN_COLUMNS)
    sanity_checks(df)
    update_run_metadata("benchmark_A", {"heuristic": "matrix_euclid_utm_round_down", "n_runs": len(df)})
    return df


def sanity_checks(df) -> None:
    """UCS khớp NetworkX, A* bằng UCS, A* không mở lại nút; vi phạm thì dừng chương trình."""
    tol = load_config("experiment")["checks"]["cost_tol_m"]
    errors = []
    for dataset, group in df.groupby("dataset"):
        G = load_processed(dataset)
        if dataset != "A":
            G = to_simple_digraph(G)
        for case_id, runs in group.groupby("case_id"):
            by_algo = runs.set_index("algorithm")
            ucs_row = by_algo.loc["UCS"]
            nx_m = nx.shortest_path_length(G, ucs_row["source"], ucs_row["target"], weight="length")
            if abs(ucs_row["path_m"] - nx_m) > tol:
                errors.append(f"{dataset}/{case_id}: UCS {ucs_row['path_m']:.3f} ≠ NetworkX {nx_m:.3f}")
            if "ASTAR" in by_algo.index:
                astar_row = by_algo.loc["ASTAR"]
                if abs(astar_row["path_m"] - ucs_row["path_m"]) > tol:
                    errors.append(f"{dataset}/{case_id}: A* {astar_row['path_m']:.3f} ≠ UCS {ucs_row['path_m']:.3f}")
                if astar_row["reopened"] != 0:
                    errors.append(f"{dataset}/{case_id}: A* reopened = {astar_row['reopened']}")
    if errors:
        raise SystemExit("sanity_checks thất bại:\n" + "\n".join(errors))
