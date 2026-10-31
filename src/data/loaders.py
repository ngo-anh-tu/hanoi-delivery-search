"""Cầu nối duy nhất giữa OSMnx/NetworkX và module search."""

import networkx as nx
import osmnx as ox
import pandas as pd

from src.config import PATHS
from src.search.graph import SearchGraph

_NODE_DTYPES = {"lat": float, "lon": float}


def load_processed(name):
    """Đọc data/processed/<name>.graphml (MultiDiGraph cho B1/B2, Graph cho A)."""
    path = PATHS.DATA_PROCESSED / f"{name}.graphml"
    if name == "A":
        return nx.read_graphml(path)
    return ox.load_graphml(path, node_dtypes=_NODE_DTYPES)


def to_simple_digraph(G):
    """Giữ cạnh song song ngắn nhất rồi xóa self-loop."""
    D = ox.convert.to_digraph(G, weight="length")
    D.remove_edges_from(list(nx.selfloop_edges(D)))
    return D


def load_search_graph(name) -> SearchGraph:
    G = load_processed(name)
    return SearchGraph.from_networkx(G if name == "A" else to_simple_digraph(G))


def load_heuristic_matrix() -> dict:
    """Bảng h của đồ thị A dưới dạng {nút: {đích: mét}}."""
    table = pd.read_csv(PATHS.TABLES / "A_heuristic_matrix.csv", index_col=0)
    return {u: {v: float(table.loc[u, v]) for v in table.columns} for u in table.index}
