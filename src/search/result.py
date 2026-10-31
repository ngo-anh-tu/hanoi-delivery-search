"""Kết quả của một lần chạy thuật toán tìm kiếm."""

from dataclasses import dataclass


@dataclass
class SearchResult:
    algorithm: str
    source: int
    target: int
    found: bool
    path: list              # [] nếu không tìm thấy
    cost_m: float           # math.inf nếu không tìm thấy
    hops: int               # len(path) - 1, hoặc -1
    expanded: int
    generated: int
    stale_skipped: int
    reopened: int           # chỉ có nghĩa với A*
    max_frontier: int
    runtime_ms: float | None = None
    expanded_order: list | None = None   # khi trace_level là "order" hoặc "steps"
    steps: list | None = None            # khi trace_level là "steps" (chỉ đồ thị nhỏ)
