"""Cluster video titles into food concepts with the model (offline, once).

Reads titles from data/raw/youtube/*.json, asks the provider chain for concept
records, validates each against the concept schema, and writes candidates to
data/concepts.candidates.json. A human reviews them and merges good ones into
data/concepts.json by hand. Runtime never re-clusters.

    GEMINI_API_KEY=... py -3 scripts/cluster_concepts.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from leadtime.concepts import CATEGORIES, CONCEPT_SCHEMA, EQUIPMENT  # noqa: E402
from leadtime.providers import Chain  # noqa: E402
from leadtime.schema import SchemaError, validate  # noqa: E402

MAX_TITLES = 300  # one prompt's worth

SYSTEM = (
    "Group these food video titles into distinct trending food concepts.\n"
    'Reply with JSON: {"concepts": [concept, ...]} where each concept has: '
    'id (kebab-case), name, aliases (object of language code -> list of names, include native-language names), '
    f"description (one sentence), category (one of {CATEGORIES}), key_ingredients (list), "
    f"techniques (list), equipment (subset of {EQUIPMENT}).\n"
    "Ignore titles that are not a specific food. No numbers about popularity."
)


def main():
    titles = []
    for p in sorted((ROOT / "data" / "raw" / "youtube").glob("*.json")):
        raw = json.loads(p.read_text(encoding="utf-8"))
        titles += [i["snippet"]["title"] for i in raw.get("search", {}).get("items", [])]
    if not titles:
        sys.exit("No YouTube titles. Run scripts/fetch_youtube.py first.")

    def check(out):
        if not isinstance(out, dict) or not isinstance(out.get("concepts"), list):
            raise SchemaError("expected {concepts: [...]}")
        return out

    result, provider, attempts = Chain().run("cluster", SYSTEM, "\n".join(titles[:MAX_TITLES]), check)
    if not result:
        sys.exit(f"No provider answered: {attempts}")
    kept = []
    for c in result["concepts"]:
        try:
            kept.append(validate(c, CONCEPT_SCHEMA))
        except SchemaError as e:
            print(f"dropped {c.get('id')}: {e}")
    out = ROOT / "data" / "concepts.candidates.json"
    out.write_text(json.dumps({"provider": provider, "concepts": kept}, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print(f"{len(kept)} candidates from {provider} -> {out}. Review by hand before merging.")


if __name__ == "__main__":
    main()
