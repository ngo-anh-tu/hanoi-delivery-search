"""Cấu trúc đồ thị tối giản, nhanh, xác định cho các thuật toán tìm kiếm."""


class SearchGraph:
    """Danh sách kề và tọa độ. Hàng xóm của mỗi nút luôn sắp theo id tăng dần.

    Id nút là int ở mức B và chuỗi mã quận ở mức A; chỉ cần so sánh được với nhau.
    """

    def __init__(self, adj, x, y, lat=None, lon=None, name=None):
        self.adj = adj
        self.x = x
        self.y = y
        self.lat = lat or {}
        self.lon = lon or {}
        self.name = name or {}

    @classmethod
    def from_networkx(cls, G, weight="length"):
        """Dựng từ nx.DiGraph hoặc nx.Graph; với nx.Graph, G.adj cho cả hai chiều."""
        if G.is_multigraph():
            raise ValueError("SearchGraph không nhận multigraph; hãy chuyển ở src/data/loaders.py")
        adj = {u: sorted((v, float(attrs[weight])) for v, attrs in G.adj[u].items()) for u in G.nodes}

        def node_attr(attr):
            return {n: data[attr] for n, data in G.nodes(data=True) if attr in data}

        return cls(adj, node_attr("x"), node_attr("y"), node_attr("lat"), node_attr("lon"), node_attr("name"))

    @classmethod
    def from_edges(cls, nodes, edges, directed):
        """Dựng từ nodes = {id: (x, y)} và edges = [(u, v, w)]; dùng cho test."""
        best = {u: {} for u in nodes}
        for u, v, w in edges:
            best[u][v] = min(w, best[u].get(v, float("inf")))
            if not directed:
                best[v][u] = min(w, best[v].get(u, float("inf")))
        adj = {u: sorted(nbrs.items()) for u, nbrs in best.items()}
        x = {n: float(xy[0]) for n, xy in nodes.items()}
        y = {n: float(xy[1]) for n, xy in nodes.items()}
        return cls(adj, x, y)

    def neighbors(self, u):
        return self.adj[u]

    def edge_cost(self, u, v):
        for neighbor, w in self.adj[u]:
            if neighbor == v:
                return w
        raise KeyError(f"Không có cạnh {u} → {v}")

    @property
    def n_nodes(self):
        return len(self.adj)

    @property
    def n_edges(self):
        return sum(len(nbrs) for nbrs in self.adj.values())
