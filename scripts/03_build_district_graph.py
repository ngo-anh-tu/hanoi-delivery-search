"""Dựng đồ thị A (12 quận cũ) từ GADM và B2."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import ensure_dirs  # noqa: E402
from src.data.district_graph import build_district_graph  # noqa: E402


def main():
    argparse.ArgumentParser(description=__doc__).parse_args()
    ensure_dirs()
    G = build_district_graph()
    print(f"Đồ thị A: {G.number_of_nodes()} nút, {G.number_of_edges()} cạnh")
    for u, v, data in sorted(G.edges(data=True)):
        print(f"  {u}–{v}: {data['length'] / 1000:.1f} km")


if __name__ == "__main__":
    main()
