"""Demo web: so sánh BFS, GBFS, A*, UCS trên bản đồ Hà Nội (nút đã mở rộng, nút đang mở, đường đi)."""

import json
import queue
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np  # noqa: E402
from flask import Flask, Response, jsonify, request, send_from_directory  # noqa: E402

from src.config import PATHS, load_config  # noqa: E402
from src.data.loaders import load_search_graph  # noqa: E402
from src.search import ALGORITHMS, run  # noqa: E402
from src.search.common import set_expand_hook, timed_run  # noqa: E402

STATIC = Path(__file__).resolve().parent / "static"
DATASETS = ["B1", "B2"]
LABELS = {"B1": "B1 — mạng chi tiết (ô tô)", "B2": "B2 — mạng trục chính"}

app = Flask(__name__, static_folder=None)
_cache = {}


class GraphData:
    """SearchGraph kèm bảng id <-> chỉ số để gửi cho trình duyệt dưới dạng số nguyên nhỏ."""

    def __init__(self, name):
        self.sg = load_search_graph(name)
        self.ids = list(self.sg.adj)
        self.index = {n: i for i, n in enumerate(self.ids)}
        self.lat = np.array([self.sg.lat[n] for n in self.ids])
        self.lon = np.array([self.sg.lon[n] for n in self.ids])
        self.cos_lat = float(np.cos(np.radians(self.lat.mean())))

    def snap(self, lat, lon):
        """Nút gần nhất (id nút, khoảng cách mét)."""
        dy = np.radians(self.lat - lat)
        dx = np.radians(self.lon - lon) * self.cos_lat
        d2 = dx * dx + dy * dy
        i = int(d2.argmin())
        return self.ids[i], float(np.sqrt(d2[i]) * 6_371_009)


def graph(name):
    if name not in _cache:
        _cache[name] = GraphData(name)
    return _cache[name]


def available():
    return [n for n in DATASETS if (PATHS.DATA_PROCESSED / f"{n}.graphml").exists()]


@app.get("/")
def index():
    return send_from_directory(STATIC, "index.html")


@app.get("/api/meta")
def meta():
    cfg = load_config("locations")
    places = lambda group: [  # noqa: E731
        {"id": k, "name": v["query"].split(",")[0], "lat": v["latlon"][0], "lon": v["latlon"][1]}
        for k, v in cfg[group].items()
        if v.get("latlon")
    ]
    return jsonify(
        datasets=[{"id": n, "label": LABELS[n]} for n in available()],
        depots=places("depots"),
        targets=places("targets"),
        algorithms=list(ALGORITHMS),
    )


@app.get("/api/graph/<name>")
def graph_nodes(name):
    if name not in available():
        return jsonify(error=f"Chưa có data/processed/{name}.graphml"), 404
    g = graph(name)
    return jsonify(lat=np.round(g.lat, 5).tolist(), lon=np.round(g.lon, 5).tolist())


class _Stop(Exception):
    pass


def _line(obj):
    return json.dumps(obj, separators=(",", ":")) + "\n"


@app.post("/api/run")
def run_live():
    """Chạy các thuật toán song song và stream NDJSON: mỗi dòng là một lô nút mở rộng/nút mới mở."""
    body = request.get_json()
    name = body["dataset"]
    if name not in available():
        return jsonify(error=f"Chưa có data/processed/{name}.graphml"), 404
    g = graph(name)
    s, s_dist = g.snap(body["source"]["lat"], body["source"]["lon"])
    t, t_dist = g.snap(body["target"]["lat"], body["target"]["lon"])
    heuristic = load_config("experiment")["heuristic"]
    algos = body.get("algorithms", list(ALGORITHMS))
    rate = max(50.0, float(body.get("rate", 1500)))  # nút mở rộng mỗi giây, như nhau cho mọi thuật toán
    chunk = max(1, int(rate * 0.04))
    q = queue.Queue()
    stop = threading.Event()

    def worker(algo):
        expanded, opened, seen, count = [], [], {s}, [0]
        t0 = time.perf_counter()

        def flush():
            if expanded:
                q.put({"algo": algo, "expanded": expanded[:], "opened": opened[:]})
                expanded.clear()
                opened.clear()

        def hook(u):
            if stop.is_set():
                raise _Stop
            expanded.append(g.index[u])
            for v, _ in g.sg.neighbors(u):
                if v not in seen:
                    seen.add(v)
                    opened.append(g.index[v])
            count[0] += 1
            if count[0] % chunk == 0:
                flush()
                delay = t0 + count[0] / rate - time.perf_counter()
                if delay > 0:
                    time.sleep(delay)

        set_expand_hook(hook)
        try:
            r = run(algo, g.sg, s, t, heuristic)
            flush()
            q.put({"algo": algo, "done": True, "found": r.found, "path": [g.index[n] for n in r.path],
                   "cost_m": r.cost_m if r.found else None, "hops": r.hops,
                   "expanded_n": r.expanded, "generated": r.generated})  # fmt: skip
        except _Stop:
            q.put({"algo": algo, "done": True, "stopped": True})
        finally:
            set_expand_hook(None)

    def stream():
        yield _line({"start": True, "source": g.index[s], "target": g.index[t],
                     "snap_m": {"source": s_dist, "target": t_dist}})  # fmt: skip
        threads = [threading.Thread(target=worker, args=(a,), daemon=True) for a in algos]
        try:
            for th in threads:
                th.start()
            finished = 0
            while finished < len(algos):
                item = q.get()
                finished += bool(item.get("done"))
                yield _line(item)
            # Thời gian thật: chạy lại không giãn nhịp, không hook.
            timing = {a: timed_run(run, a, g.sg, s, t, heuristic, warmup=0, repeats=3)[1] for a in algos}
            yield _line({"timing": timing})
        finally:
            stop.set()

    return Response(stream(), mimetype="application/x-ndjson", headers={"X-Accel-Buffering": "no"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
