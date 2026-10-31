"""Giá trị kỳ vọng trên đồ thị đồ chơi, đã tính tay (mục 9.2 của đặc tả)."""

import pytest

from src.search import run


@pytest.mark.parametrize(
    "algorithm, path, cost, hops, expanded",
    [
        ("BFS", [0, 4, 5], 1000, 2, 5),
        ("UCS", [0, 1, 2, 3, 5], 400, 4, 5),
        ("ASTAR", [0, 1, 2, 3, 5], 400, 4, 5),
    ],
)
def test_bfs_bias(toy_bfs_bias, algorithm, path, cost, hops, expanded):
    result = run(algorithm, toy_bfs_bias, 0, 5)
    assert result.path == path
    assert result.cost_m == cost
    assert result.hops == hops
    assert result.expanded == expanded


@pytest.mark.parametrize(
    "algorithm, path, cost, hops, expanded",
    [
        ("BFS", [0, 1, 4], 2900, 2, 4),
        ("GBFS", [0, 1, 4], 2900, 2, 3),
        ("ASTAR", [0, 2, 3, 4], 2200, 3, 5),
        ("UCS", [0, 2, 3, 4], 2200, 3, 5),
    ],
)
def test_gbfs_trap(toy_gbfs_trap, algorithm, path, cost, hops, expanded):
    result = run(algorithm, toy_gbfs_trap, 0, 4)
    assert result.path == path
    assert result.cost_m == cost
    assert result.hops == hops
    assert result.expanded == expanded
