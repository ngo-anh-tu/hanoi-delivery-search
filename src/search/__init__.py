"""Registry thuật toán tìm kiếm. Module này không biết gì về OSMnx hay Hà Nội."""

from src.search.astar import astar
from src.search.bfs import bfs
from src.search.gbfs import gbfs
from src.search.graph import SearchGraph
from src.search.heuristics import get_heuristic
from src.search.result import SearchResult
from src.search.ucs import ucs, ucs_all

ALGORITHMS = {"BFS": bfs, "GBFS": gbfs, "ASTAR": astar, "UCS": ucs}
_INFORMED = {"GBFS", "ASTAR"}


def run(name, sg, s, t, heuristic_name="euclid_utm", trace_level="none"):
    """Chạy thuật toán theo tên; tự tạo h cho GBFS/A*.

    heuristic_name là tên trong heuristics, hoặc hàm (sg, target) -> h.
    """
    fn = ALGORITHMS[name]
    if name in _INFORMED:
        return fn(sg, s, t, get_heuristic(heuristic_name)(sg, t), trace_level=trace_level)
    return fn(sg, s, t, trace_level=trace_level)


__all__ = ["ALGORITHMS", "SearchGraph", "SearchResult", "astar", "bfs", "gbfs", "run", "ucs", "ucs_all"]
