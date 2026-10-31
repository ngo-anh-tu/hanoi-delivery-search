"""Kiểm chứng bằng số tính consistent của heuristic trên đồ thị thật."""

import random

import pytest

from src.config import PATHS, load_config
from src.data.loaders import load_heuristic_matrix, load_search_graph
from src.search.heuristics import get_heuristic

N_TARGETS = 20
TOLERANCE_M = 1e-6


def _require(name):
    if not (PATHS.DATA_PROCESSED / f"{name}.graphml").exists():
        pytest.skip(f"chưa có data/processed/{name}.graphml")


@pytest.mark.parametrize("name", ["B1", "B2"])
def test_configured_heuristic_is_consistent_on_every_edge(name):
    _require(name)
    sg = load_search_graph(name)
    make_h = get_heuristic(load_config("experiment")["heuristic"])
    targets = random.Random(42).sample(sorted(sg.adj), N_TARGETS)
    for target in targets:
        h = make_h(sg, target)
        for u, neighbors in sg.adj.items():
            h_u = h(u)
            for v, cost in neighbors:
                assert h_u <= cost + h(v) + TOLERANCE_M, f"{u} → {v}, đích {target}"


def test_level_a_heuristic_is_consistent():
    _require("A")
    sg = load_search_graph("A")
    matrix = load_heuristic_matrix()
    for u, neighbors in sg.adj.items():
        for v, weight in neighbors:
            assert weight >= matrix[u][v]
            for target in sg.adj:
                assert matrix[u][target] <= weight + matrix[v][target] + TOLERANCE_M


@pytest.mark.parametrize("name", ["B1", "B2"])
def test_euclid_utm_exceeds_edge_length_somewhere(name):
    """Lý do không dùng euclid_utm: length tính trên mặt cầu, UTM chiếu từ ellipsoid (design.md mục 2.2)."""
    _require(name)
    sg = load_search_graph(name)
    violations = sum(
        get_heuristic("euclid_utm")(sg, v)(u) > cost + TOLERANCE_M
        for u, neighbors in sg.adj.items()
        for v, cost in neighbors
    )
    assert violations > 0
