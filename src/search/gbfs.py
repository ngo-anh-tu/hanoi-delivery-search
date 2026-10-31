"""Greedy Best-First Search (graph search): f(n) = h(n)."""

import math

from src.search.common import PriorityFrontier, Tracer, live_frontier, path_cost, reconstruct_path
from src.search.result import SearchResult


def gbfs(sg, s, t, h, trace_level="none"):
    tracer = Tracer(trace_level, sg.n_nodes)
    frontier = PriorityFrontier()
    frontier.push(h(s), s)
    seen = {s}
    parent = {s: None}
    closed = set()
    expanded = 0
    generated = 1
    stale_skipped = 0
    max_frontier = 1
    found = False

    while frontier:
        priority, u = frontier.pop()
        if u in closed:
            stale_skipped += 1
            continue
        closed.add(u)
        expanded += 1
        tracer.expand(u)
        found = u == t
        if not found:
            for v, _ in sg.neighbors(u):
                if v not in seen:  # chỉ lần đầu nhìn thấy, cha cố định từ đó
                    seen.add(v)
                    parent[v] = u
                    frontier.push(h(v), v)
                    generated += 1
        max_frontier = max(max_frontier, len(frontier))
        if tracer.wants_steps:
            g = path_cost(sg, reconstruct_path(parent, s, u))
            tracer.step(u, g, priority, priority, live_frontier(frontier.items(), closed), closed)
        if found:
            break

    path = reconstruct_path(parent, s, t) if found else []
    return SearchResult(
        algorithm="GBFS",
        source=s,
        target=t,
        found=found,
        path=path,
        cost_m=path_cost(sg, path) if found else math.inf,
        hops=len(path) - 1,
        expanded=expanded,
        generated=generated,
        stale_skipped=stale_skipped,
        reopened=0,
        max_frontier=max_frontier,
        expanded_order=tracer.expanded_order,
        steps=tracer.steps,
    )
