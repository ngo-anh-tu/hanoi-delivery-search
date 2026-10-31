"""Kịch bản nhiều điểm dừng: chọn thứ tự bằng Nearest-Neighbor, mỗi chặng tìm đường bằng A*."""

import math
from dataclasses import dataclass

from src.search import run, ucs_all


@dataclass
class TourResult:
    legs: list          # SearchResult của từng chặng
    total_m: float
    total_expanded: int


def nearest_neighbor_order(sg, depot, customers, rule) -> list:
    """Trả [kho, khách đầu tiên, ...]; rule là "euclid" (chim bay) hoặc "road" (đường bộ)."""
    order = [depot]
    remaining = list(customers)
    while remaining:
        current = order[-1]
        if rule == "euclid":
            cx, cy = sg.x[current], sg.y[current]
            distance = {c: math.hypot(sg.x[c] - cx, sg.y[c] - cy) for c in remaining}
        elif rule == "road":
            dist = ucs_all(sg, current)
            distance = {c: dist.get(c, math.inf) for c in remaining}
        else:
            raise ValueError(f"order_rule không hợp lệ: {rule}")
        # Phá hòa theo thứ tự trong danh sách khách.
        chosen = min(remaining, key=lambda c: distance[c])
        order.append(chosen)
        remaining.remove(chosen)
    return order


def route_tour(sg, order, return_to_depot, algorithm="ASTAR", heuristic="haversine") -> TourResult:
    """Ghép các chặng theo order; order[0] là kho."""
    stops = list(order) + ([order[0]] if return_to_depot else [])
    legs = [run(algorithm, sg, a, b, heuristic) for a, b in zip(stops, stops[1:])]
    return TourResult(legs, sum(leg.cost_m for leg in legs), sum(leg.expanded for leg in legs))
