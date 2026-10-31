"""A* phải bằng UCS và bằng NetworkX trên các cặp ngẫu nhiên của đồ thị thật."""

import random
import warnings

import networkx as nx
import pytest

from src.config import PATHS, load_config
from src.data.loaders import load_processed, to_simple_digraph
from src.search import SearchGraph, run

TOL_M = load_config("experiment")["checks"]["cost_tol_m"]


@pytest.mark.parametrize("name, n_pairs", [("B2", 30), ("B1", 10)])
def test_astar_matches_ucs_and_networkx(name, n_pairs):
    if not (PATHS.DATA_PROCESSED / f"{name}.graphml").exists():
        pytest.skip(f"chưa có data/processed/{name}.graphml")
    G = to_simple_digraph(load_processed(name))
    sg = SearchGraph.from_networkx(G)
    heuristic = load_config("experiment")["heuristic"]
    rng = random.Random(42)
    nodes = sorted(sg.adj)
    for _ in range(n_pairs):
        s, t = rng.choice(nodes), rng.choice(nodes)
        astar = run("ASTAR", sg, s, t, heuristic)
        ucs = run("UCS", sg, s, t)
        nx_m = nx.shortest_path_length(G, s, t, weight="length")
        assert astar.cost_m == pytest.approx(ucs.cost_m, abs=TOL_M)
        assert ucs.cost_m == pytest.approx(nx_m, abs=TOL_M)
        assert astar.reopened == 0
        if astar.expanded > ucs.expanded:
            # Có thể lệch vài nút do phá hòa nên chỉ cảnh báo.
            warnings.warn(f"{name} {s}→{t}: A* mở {astar.expanded} nút > UCS {ucs.expanded} nút")
