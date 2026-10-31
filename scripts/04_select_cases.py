"""Chọn và kiểm tra các ca thử, sinh đích ngẫu nhiên, ghi cases.csv."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import ensure_dirs  # noqa: E402
from src.experiments.select_cases import select_all  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="all", choices=["B1", "B2", "all"])
    args = parser.parse_args()

    ensure_dirs()
    table = select_all(None if args.dataset == "all" else [args.dataset])
    named = table[table["property"] != "random"]
    columns = ["dataset", "case_id", "target_id", "snap_dist_m", "d_euclid_m", "detour", "check_status", "auto_replaced", "note"]
    print(named[columns].round(2).to_string(index=False))
    print(table[table["property"] == "random"].groupby("dataset").size().rename("n_random").to_string())


if __name__ == "__main__":
    main()
