"""A*: f(n) = g(n) + h(n)."""

import math

from src.search.common import PriorityFrontier, Tracer, live_frontier, reconstruct_path
from src.search.result import SearchResult

# Sai số làm tròn số thực khi cộng dồn g không được tính là một lần mở lại nút.
REOPEN_EPS_M = 1e-9


def astar(sg, s, t, h, trace_level="none", algorithm="ASTAR"):
    tracer = Tracer(trace_level, sg.n_nodes)
    frontier = PriorityFrontier()
    frontier.push(h(s), s)
    g = {s: 0.0}
    parent = {s: None}
    closed = set()
    expanded = 0
    generated = 1
    stale_skipped = 0
    reopened = 0
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
            g_u = g[u]
            for v, w in sg.neighbors(u):
                g_new = g_u + w
                if v in closed:
                    if g_new < g[v] - REOPEN_EPS_M:
                        reopened += 1  # không được xảy ra với h consistent
                    continue
                if g_new < g.get(v, math.inf):
                    g[v] = g_new
                    parent[v] = u
                    frontier.push(g_new + h(v), v)
                    generated += 1
        max_frontier = max(max_frontier, len(frontier))
        if tracer.wants_steps:
            tracer.step(u, g[u], h(u), priority, live_frontier(frontier.items(), closed), closed)
        if found:
            break

    path = reconstruct_path(parent, s, t) if found else []
    return SearchResult(
        algorithm=algorithm,
        source=s,
        target=t,
        found=found,
        path=path,
        cost_m=g[t] if found else math.inf,
        hops=len(path) - 1,
        expanded=expanded,
        generated=generated,
        stale_skipped=stale_skipped,
        reopened=reopened,
        max_frontier=max_frontier,
        expanded_order=tracer.expanded_order,
        steps=tracer.steps,
    )
