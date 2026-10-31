"""Các hàm heuristic. Mỗi hàm nhận (sg, target) và trả h: nút -> mét."""

import math

EARTH_RADIUS_M = 6_371_009  # cùng bán kính OSMnx dùng để tính thuộc tính length


def euclid_utm(sg, target):
    """Khoảng cách Euclid trên tọa độ đã chiếu."""
    xs, ys = sg.x, sg.y
    tx, ty = xs[target], ys[target]
    return lambda n: math.hypot(xs[n] - tx, ys[n] - ty)


def haversine(sg, target):
    """Khoảng cách great-circle trên mặt cầu."""
    lats, lons = sg.lat, sg.lon
    t_lat = math.radians(lats[target])
    t_lon = math.radians(lons[target])
    cos_t_lat = math.cos(t_lat)

    def h(n):
        lat = math.radians(lats[n])
        d_lat = lat - t_lat
        d_lon = math.radians(lons[n]) - t_lon
        a = math.sin(d_lat / 2) ** 2 + math.cos(lat) * cos_t_lat * math.sin(d_lon / 2) ** 2
        return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(min(a, 1.0)))

    return h


def zero(sg, target):
    """Luôn bằng 0 (cho UCS)."""
    return lambda n: 0.0


def from_matrix(matrix, target):
    """Tra bảng {nút: {đích: h}} (đồ thị A, đã làm tròn xuống)."""
    return lambda n: matrix[n][target]


_HEURISTICS = {"euclid_utm": euclid_utm, "haversine": haversine, "zero": zero}


def get_heuristic(name):
    """Chọn heuristic theo tên trong experiment.yaml; hàm (sg, target) -> h được giữ nguyên."""
    if callable(name):
        return name
    return _HEURISTICS[name]
