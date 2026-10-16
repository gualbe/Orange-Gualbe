"""Compare two large_data.py result files: python compare.py before.json after.json"""
import json
import sys


def main(before_path, after_path):
    with open(before_path) as f:
        before = json.load(f)
    with open(after_path) as f:
        after = json.load(f)
    print(f"before: {before['meta']['rev']} ({before['meta']['rows']} rows)")
    print(f"after:  {after['meta']['rev']} ({after['meta']['rows']} rows)\n")
    print(f"{'benchmark':30s} {'before':>10s} {'after':>10s} {'speedup':>8s}")
    for name, b in before["results"].items():
        a = after["results"].get(name)
        if a is None or "time" not in a or "time" not in b:
            continue
        ratio = b["time"] / a["time"] if a["time"] else float("inf")
        flag = "  <<" if ratio < 0.9 else "  ++" if ratio > 1.1 else ""
        print(f"{name:30s} {b['time']:10.4f} {a['time']:10.4f} "
              f"{ratio:7.2f}x{flag}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
