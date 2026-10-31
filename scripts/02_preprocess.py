"""Làm sạch và chiếu đồ thị: LSCC → UTM 48N → thống kê."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import ensure_dirs  # noqa: E402
from src.data.preprocess import preprocess_dataset  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="all", choices=["B1", "B2", "all"])
    args = parser.parse_args()

    ensure_dirs()
    names = ["B1", "B2"] if args.dataset == "all" else [args.dataset]
    for name in names:
        print(f"Đã lưu {name}: {preprocess_dataset(name)}")


if __name__ == "__main__":
    main()
