"""Chạy thuật toán × ca × đồ thị rồi tổng hợp kết quả."""

import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import PATHS, ensure_dirs  # noqa: E402
from src.experiments.analyze import analyze_all  # noqa: E402
from src.experiments.benchmark import run_dataset, run_level_A  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="all", choices=["B1", "B2", "all"])
    parser.add_argument("--skip-A", action="store_true", help="không chạy mức A")
    parser.add_argument("--no-traces", action="store_true", help="không lưu trace")
    args = parser.parse_args()

    ensure_dirs()
    names = ["B1", "B2"] if args.dataset == "all" else [args.dataset]
    runs_path = PATHS.TABLES / "runs.csv"
    frames = [run_dataset(name, save_traces=not args.no_traces) for name in names]
    if runs_path.exists():
        old = pd.read_csv(runs_path)
        frames.insert(0, old[~old["dataset"].isin(names)])
    pd.concat(frames, ignore_index=True).sort_values("dataset", kind="stable").to_csv(runs_path, index=False)
    print(f"Đã ghi {runs_path}; sanity_checks qua hết")

    if not args.skip_A:
        run_level_A(save_traces=not args.no_traces).to_csv(PATHS.TABLES / "runs_A.csv", index=False)
        print("Đã ghi runs_A.csv; sanity_checks qua hết")

    tables = analyze_all()
    for title, table in tables.items():
        print(f"\n{title}\n{table.to_string(index=False)}")


if __name__ == "__main__":
    main()
