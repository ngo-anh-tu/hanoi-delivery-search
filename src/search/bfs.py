"""Breadth-First Search: coi mọi cạnh có chi phí bằng nhau."""

import math
from collections import deque

from src.search.common import Tracer, path_cost, reconstruct_path
from src.search.result import SearchResult


def bfs(sg, s, t, trace_level="none"):
    tracer = Tracer(trace_level, sg.n_nodes)
    queue = deque([s])
    seen = {s}
    parent = {s: None}
    expanded = 0
    generated = 1
    max_frontier = 1
    found = False

    while queue:
        u = queue.popleft()
        expanded += 1
        tracer.expand(u)
        found = u == t  # kiểm tra đích khi rút ra
        if not found:
            for v, _ in sg.neighbors(u):
                if v not in seen:
                    seen.add(v)
                    parent[v] = u
                    queue.append(v)
                    generated += 1
        max_frontier = max(max_frontier, len(queue))
        if tracer.wants_steps:
            g = path_cost(sg, reconstruct_path(parent, s, u))
            tracer.step(u, g, None, None, [(v, None) for v in queue], tracer.expanded_order)
        if found:
            break

    path = reconstruct_path(parent, s, t) if found else []
    return SearchResult(
        algorithm="BFS",
        source=s,
        target=t,
        found=found,
        path=path,
        cost_m=path_cost(sg, path) if found else math.inf,
        hops=len(path) - 1,
        expanded=expanded,
        generated=generated,
        stale_skipped=0,
        reopened=0,
        max_frontier=max_frontier,
        expanded_order=tracer.expanded_order,
        steps=tracer.steps,
    )
