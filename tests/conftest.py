"""Đồ thị đồ chơi dùng chung; tọa độ tính bằng mét, h hợp lệ trên mọi đồ thị."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.search import SearchGraph  # noqa: E402


@pytest.fixture
def toy_bfs_bias():
    """BFS chọn đường ít cạnh nhưng dài."""
    nodes = {0: (0, 0), 1: (75, 0), 2: (150, 0), 3: (225, 0), 4: (150, 400), 5: (300, 0)}
    edges = [(0, 1, 100), (1, 2, 100), (2, 3, 100), (3, 5, 100), (0, 4, 500), (4, 5, 500)]
    return SearchGraph.from_edges(nodes, edges, directed=False)


@pytest.fixture
def toy_gbfs_trap():
    """"Con sông": nút 1 rất gần đích theo chim bay nhưng cạnh 1–4 phải vòng xa."""
    nodes = {0: (0, 0), 1: (900, 0), 2: (0, 600), 3: (1000, 600), 4: (1000, 0)}
    edges = [(0, 1, 900), (1, 4, 2000), (0, 2, 600), (2, 3, 1000), (3, 4, 600)]
    return SearchGraph.from_edges(nodes, edges, directed=False)


@pytest.fixture
def toy_stale():
    """Có hướng, mọi nút cùng tọa độ nên h ≡ 0."""
    nodes = {n: (0, 0) for n in range(5)}
    edges = [(0, 1, 5), (0, 2, 1), (2, 1, 1), (1, 3, 1), (3, 4, 10)]
    return SearchGraph.from_edges(nodes, edges, directed=True)


@pytest.fixture
def toy_grid():
    """Lưới 3 × 3, nhiều đường cùng chi phí, dùng để kiểm tra phá hòa."""
    nodes = {3 * row + col: (100 * col, 100 * row) for row in range(3) for col in range(3)}
    edges = []
    for row in range(3):
        for col in range(3):
            n = 3 * row + col
            if col < 2:
                edges.append((n, n + 1, 100))
            if row < 2:
                edges.append((n, n + 3, 100))
    return SearchGraph.from_edges(nodes, edges, directed=False)
