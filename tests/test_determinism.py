"""Tính xác định: cùng đầu vào cho cùng thứ tự mở rộng và cùng đường đi."""

import pytest

from src.search import ALGORITHMS, SearchGraph, run


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_two_runs_identical(toy_grid, algorithm):
    first = run(algorithm, toy_grid, 0, 8, trace_level="order")
    second = run(algorithm, toy_grid, 0, 8, trace_level="order")
    assert first.expanded_order == second.expanded_order
    assert first.path == second.path


def test_neighbors_sorted_by_id(toy_grid):
    for neighbors in toy_grid.adj.values():
        ids = [v for v, _ in neighbors]
        assert ids == sorted(ids)


def test_neighbors_sorted_regardless_of_edge_order():
    sg = SearchGraph.from_edges(
        {0: (0, 0), 1: (1, 0), 2: (2, 0), 3: (3, 0)},
        [(0, 3, 3), (0, 1, 1), (0, 2, 2)],
        directed=True,
    )
    assert [v for v, _ in sg.neighbors(0)] == [1, 2, 3]
