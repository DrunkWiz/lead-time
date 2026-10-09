"""Tuesday gate: print takeoff week per region and the SG lag for each concept.

    py -3 scripts/check_cases.py [concept_id ...]
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from leadtime import data  # noqa: E402
from leadtime.forecast import HOME, origin_of, takeoffs, weeks_between  # noqa: E402


def main():
    snap, as_of = data.snapshot(), data.snapshot_date()
    want = set(sys.argv[1:])
    for c in data.concepts():
        if want and c["id"] not in want:
            continue
        tk = takeoffs(snap["weeks"], snap["series"].get(c["id"], {}), as_of)
        og, ow = origin_of(tk)
        lag = weeks_between(ow, tk[HOME]) if og and HOME in tk else None
        regions = "  ".join(f"{g}:{w}" for g, w in sorted(tk.items(), key=lambda x: x[1]))
        lag_s = "" if lag is None else str(lag)
        print(f"{c['id']:<27} lag={lag_s:<5} {regions or '(no takeoff anywhere)'}")


if __name__ == "__main__":
    main()
