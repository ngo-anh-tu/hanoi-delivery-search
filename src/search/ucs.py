"""Uniform-Cost Search (Dijkstra): đáp án chuẩn để kiểm chứng A*."""

import heapq
import math

from src.search.astar import astar
from src.search.heuristics import zero


def ucs(sg, s, t, trace_level="none"):
    """A* với h ≡ 0."""
    return astar(sg, s, t, zero(sg, t), trace_level=trace_level, algorithm="UCS")


def ucs_all(sg, s):
    """Dijkstra một nguồn đến mọi nút, không dừng ở đích; trả {nút: khoảng cách}."""
    dist = {s: 0.0}
    closed = set()
    heap = [(0.0, 0, s)]
    counter = 1
    while heap:
        d_u, _, u = heapq.heappop(heap)
        if u in closed:
            continue
        closed.add(u)
        for v, w in sg.neighbors(u):
            d_new = d_u + w
            if d_new < dist.get(v, math.inf):
                dist[v] = d_new
                heapq.heappush(heap, (d_new, counter, v))
                counter += 1
    return dist
