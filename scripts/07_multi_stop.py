"""Kịch bản nhiều điểm dừng: so sánh hai cách chọn thứ tự khách."""

import argparse
import sys
from pathlib import Path

import folium
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import PATHS, ensure_dirs, load_config, update_run_metadata  # noqa: E402
from src.data.loaders import load_processed, load_search_graph  # noqa: E402
from src.data.locations import resolve_all  # noqa: E402
from src.routing.multi_stop import nearest_neighbor_order, route_tour  # noqa: E402
from src.viz.expansion_maps import ROUTE_COLOR, base_map, path_latlon  # noqa: E402


def tour_map(G, tour, stops) -> folium.Map:
    """Đường đi của cả tour; mỗi điểm dừng được đánh số theo thứ tự ghé."""
    points = [point for leg in tour.legs for point in path_latlon(G, leg.path)]
    center = [sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)]
    m = base_map(center, 12, prefer_canvas=False)
    folium.PolyLine(points, color=ROUTE_COLOR, weight=4).add_to(m)
    for index, (point_id, node) in enumerate(stops):
        data = G.nodes[node]
        folium.Marker(
            [data["lat"], data["lon"]],
            tooltip=f"{index}. {point_id}",
            icon=folium.Icon(color="blue" if index == 0 else "red"),
        ).add_to(m)
    return m


def run_scenario(name) -> pd.DataFrame:
    scenario = load_config("locations")["multi_stop"][name]
    heuristic = load_config("experiment")["heuristic"]
    rows = []
    for dataset in load_config("experiment")["datasets"]:
        G = load_processed(dataset)
        sg = load_search_graph(dataset)
        points = resolve_all(None, dataset, G).set_index("point_id")
        depot = int(points.loc[scenario["depot"], "node"])
        customers = {cid: int(points.loc[cid, "node"]) for cid in scenario["customers"]}
        id_of = {node: cid for cid, node in customers.items()} | {depot: scenario["depot"]}

        for rule in scenario["order_rules"]:
            order = nearest_neighbor_order(sg, depot, list(customers.values()), rule)
            astar_tour = route_tour(sg, order, scenario["return_to_depot"], "ASTAR", heuristic)
            ucs_tour = route_tour(sg, order, scenario["return_to_depot"], "UCS", heuristic)
            rows.append(
                {
                    "scenario": name,
                    "dataset": dataset,
                    "order_rule": rule,
                    "order": " → ".join(id_of[node] for node in order),
                    "total_m": round(astar_tour.total_m, 2),
                    "total_expanded_astar": astar_tour.total_expanded,
                    "total_expanded_ucs": ucs_tour.total_expanded,
                }
            )
            stops = [(id_of[node], node) for node in order]
            tour_map(G, astar_tour, stops).save(PATHS.MAPS / f"{name}_{dataset}_{rule}.html")
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default="M1")
    args = parser.parse_args()

    ensure_dirs()
    table = run_scenario(args.scenario)
    table.to_csv(PATHS.TABLES / "multistop.csv", index=False)
    update_run_metadata("multi_stop", {"scenario": args.scenario, "n_rows": len(table)})
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
