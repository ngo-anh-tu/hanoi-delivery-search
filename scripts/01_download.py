"""Tải đồ thị B1, B2 từ OpenStreetMap vào data/raw."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import ensure_dirs  # noqa: E402
from src.data.download import download_dataset  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="all", choices=["B1", "B2", "all"])
    parser.add_argument("--force", action="store_true", help="tải lại dù đã có snapshot")
    args = parser.parse_args()

    ensure_dirs()
    names = ["B1", "B2"] if args.dataset == "all" else [args.dataset]
    for name in names:
        print(f"Đã lưu {name}: {download_dataset(name, force=args.force)}")


if __name__ == "__main__":
    main()
