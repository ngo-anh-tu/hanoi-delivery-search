"""Phần dùng chung: dựng đường, tính chi phí, frontier, trace, đo thời gian."""

import heapq
import statistics
import threading
import time

MAX_STEPS_NODES = 200

_hooks = threading.local()


def set_expand_hook(fn):
    """Đăng ký fn(node), gọi mỗi lần một nút được mở rộng, cho các Tracer tạo sau trong luồng này.

    Dùng để quan sát tiến trình trực tiếp (demo web); truyền None để gỡ.
    """
    _hooks.fn = fn


def reconstruct_path(parent, source, target):
    """Đi ngược từ target theo parent về source."""
    path = [target]
    while path[-1] != source:
        path.append(parent[path[-1]])
    path.reverse()
    return path


def path_cost(sg, path):
    """Cộng edge_cost dọc đường."""
    return sum(sg.edge_cost(u, v) for u, v in zip(path, path[1:]))


class PriorityFrontier:
    """Heap các bộ (priority, counter, node); counter tăng dần để phá hòa FIFO."""

    def __init__(self):
        self._heap = []
        self._counter = 0

    def push(self, priority, node):
        heapq.heappush(self._heap, (priority, self._counter, node))
        self._counter += 1

    def pop(self):
        priority, _, node = heapq.heappop(self._heap)
        return priority, node

    def __len__(self):
        return len(self._heap)

    def items(self):
        """Các mục (node, priority) theo đúng thứ tự sẽ được rút ra, kể cả mục cũ."""
        return [(node, priority) for priority, _, node in sorted(self._heap)]


class Tracer:
    """Ghi lại quá trình tìm kiếm; level là "none", "order" hoặc "steps"."""

    def __init__(self, level, n_nodes):
        if level not in ("none", "order", "steps"):
            raise ValueError(f"trace_level không hợp lệ: {level}")
        if level == "steps" and n_nodes > MAX_STEPS_NODES:
            raise ValueError(f"trace_level='steps' chỉ dùng cho đồ thị ≤ {MAX_STEPS_NODES} nút (có {n_nodes})")
        self.level = level
        self.wants_steps = level == "steps"
        self.expanded_order = [] if level != "none" else None
        self._hook = getattr(_hooks, "fn", None)
        self.steps = [] if self.wants_steps else None

    def expand(self, node):
        if self._hook is not None:
            self._hook(node)
        if self.expanded_order is not None:
            self.expanded_order.append(node)

    def step(self, popped, g, h, f, frontier, closed):
        """Ghi trạng thái sau một bước; frontier là [(node, f)] đã sắp, không còn mục cũ."""
        self.steps.append(
            {
                "step": len(self.steps) + 1,
                "popped": popped,
                "g": g,
                "h": h,
                "f": f,
                "frontier": [list(entry) for entry in frontier],
                "closed": sorted(closed),
            }
        )


def live_frontier(items, closed):
    """Bỏ mục đã đóng và mục trùng (mục rút sau của cùng một nút là mục cũ)."""
    seen = set()
    live = []
    for node, priority in items:
        if node not in closed and node not in seen:
            seen.add(node)
            live.append((node, priority))
    return live


def timed_run(fn, *args, warmup=1, repeats=5):
    """Chạy khởi động rồi đo; trả (kết quả lần đo cuối, trung vị mili giây)."""
    for _ in range(warmup):
        fn(*args)
    samples = []
    result = None
    for _ in range(repeats):
        start = time.perf_counter()
        result = fn(*args)
        samples.append((time.perf_counter() - start) * 1000)
    median_ms = statistics.median(samples)
    result.runtime_ms = median_ms
    return result, median_ms
