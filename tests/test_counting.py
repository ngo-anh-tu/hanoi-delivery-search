"""Quy ước đếm (mục 5.2 của đặc tả)."""

import math

import pytest

from src.search import ALGORITHMS, SearchGraph, run


@pytest.mark.parametrize("algorithm", ["UCS", "ASTAR"])
def test_stale_entries_are_skipped_and_not_counted(toy_stale, algorithm):
    result = run(algorithm, toy_stale, 0, 4)
    assert result.path == [0, 2, 1, 3, 4]
    assert result.cost_m == 13
    assert result.expanded == 5
    assert result.generated == 6
    assert result.stale_skipped == 1
    assert result.max_frontier == 2
    assert result.reopened == 0


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_source_equals_target(toy_grid, algorithm):
    result = run(algorithm, toy_grid, 4, 4)
    assert result.found
    assert result.expanded == 1
    assert result.path == [4]
    assert result.cost_m == 0
    assert result.hops == 0


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_unreachable(algorithm):
    sg = SearchGraph.from_edges({0: (0, 0), 1: (10, 0)}, [(0, 1, 10)], directed=True)
    result = run(algorithm, sg, 1, 0)
    assert not result.found
    assert result.path == []
    assert result.cost_m == math.inf
    assert result.hops == -1


def test_steps_trace_refused_on_large_graph():
    nodes = {n: (n, 0) for n in range(201)}
    sg = SearchGraph.from_edges(nodes, [(n, n + 1, 1) for n in range(200)], directed=False)
    with pytest.raises(ValueError):
        run("BFS", sg, 0, 200, trace_level="steps")


@pytest.mark.parametrize("algorithm", ALGORITHMS)
def test_steps_trace_reaches_goal(toy_gbfs_trap, algorithm):
    result = run(algorithm, toy_gbfs_trap, 0, 4, trace_level="steps")
    assert len(result.steps) == result.expanded
    assert [step["popped"] for step in result.steps] == result.expanded_order
    assert result.steps[-1]["popped"] == 4


def test_steps_frontier_hides_stale_entries(toy_stale):
    steps = run("UCS", toy_stale, 0, 4, trace_level="steps").steps
    # Sau khi rút nút 2, nút 1 có hai mục trong heap (f = 2 và f = 5); chỉ hiện mục tốt hơn.
    assert steps[1]["popped"] == 2
    assert steps[1]["frontier"] == [[1, 2.0]]
