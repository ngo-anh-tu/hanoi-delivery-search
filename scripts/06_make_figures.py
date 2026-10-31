"""Sinh bản đồ và biểu đồ từ kết quả đã có."""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import PATHS, ensure_dirs, load_config  # noqa: E402
from src.data.loaders import load_processed  # noqa: E402
from src.data.locations import resolve_all  # noqa: E402
from src.viz.charts import make_all_charts  # noqa: E402
from src.viz.detour_heatmap import detour_map, detour_png  # noqa: E402
from src.viz.expansion_maps import expansion_map_html, expansion_panels_png, load_traces  # noqa: E402


def make_maps() -> None:
    cases = pd.read_csv(PATHS.TABLES / "cases.csv", keep_default_na=False)
    for dataset in load_config("experiment")["datasets"]:
        G = load_processed(dataset)
        named = cases[(cases["dataset"] == dataset) & (cases["property"] != "random")]
        for case in named.to_dict("records"):
            traces = load_traces(dataset, case["case_id"])
            if not traces:
                print(f"Bỏ qua {dataset}/{case['case_id']}: chưa có trace")
                continue
            expansion_map_html(G, traces, case).save(PATHS.MAPS / f"{dataset}_{case['case_id']}.html")
            expansion_panels_png(G, traces, case, PATHS.FIGURES / f"fig_expansions_{dataset}_{case['case_id']}.png")
            print(f"Đã vẽ {dataset}/{case['case_id']}")

        points = resolve_all(None, dataset, G).set_index("point_id")
        for depot_id in load_config("locations")["depots"]:
            table_path = PATHS.TABLES / f"detour_{dataset}_{depot_id}.csv"
            if not table_path.exists():
                continue
            detour_df = pd.read_csv(table_path)
            depot_node = int(points.loc[depot_id, "node"])
            detour_map(detour_df, G, depot_node).save(PATHS.MAPS / f"detour_{dataset}_{depot_id}.html")
            title = f"Tỉ lệ vòng trên {dataset} tính từ kho {depot_id}"
            detour_png(detour_df, G, depot_node, title, PATHS.FIGURES / f"fig_detour_{dataset}_{depot_id}.png")
            print(f"Đã vẽ detour {dataset}/{depot_id}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", default="all", choices=["maps", "charts", "all"])
    args = parser.parse_args()

    ensure_dirs()
    if args.only in ("charts", "all"):
        make_all_charts()
        print("Đã vẽ các biểu đồ")
    if args.only in ("maps", "all"):
        make_maps()


if __name__ == "__main__":
    main()
