"""Load and validate data/concepts.json."""
import json
from pathlib import Path

from .schema import SchemaError, validate

DATA = Path(__file__).resolve().parent.parent / "data"

CATEGORIES = ["dessert", "bakery", "drink", "savoury"]
EQUIPMENT = [
    "oven", "stovetop", "fryer", "blender", "espresso machine", "freezer",
    "soft-serve machine", "griddle", "moulds", "mixer", "fridge",
]
MAX_QUERY_TERMS = 5  # Google Trends compares at most 5 terms per request

CONCEPT_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "aliases", "description", "category",
                 "key_ingredients", "techniques", "equipment"],
    "properties": {
        "id": {"type": "string", "pattern": r"^[a-z0-9-]+$"},
        "name": {"type": "string", "maxLength": 60},
        "aliases": {"type": "object", "values": {"type": "array", "items": {"type": "string"}}},
        "description": {"type": "string", "maxLength": 200},
        "category": {"enum": CATEGORIES},
        "key_ingredients": {"type": "array", "items": {"type": "string"}},
        "techniques": {"type": "array", "items": {"type": "string"}},
        "equipment": {"type": "array", "items": {"enum": EQUIPMENT}},
    },
}


def query_terms(concept):
    """Aliases in file order, English first, de-duplicated, capped at 5."""
    terms = []
    for names in concept["aliases"].values():
        for n in names:
            if n not in terms:
                terms.append(n)
    return terms[:MAX_QUERY_TERMS]


def load_concepts(path=None):
    raw = json.loads(Path(path or DATA / "concepts.json").read_text(encoding="utf-8"))
    out = []
    for c in raw["concepts"]:
        try:
            validate(c, CONCEPT_SCHEMA)
        except SchemaError as exc:
            print(f"concepts.json: dropping {c.get('id')}: {exc}")
            continue
        out.append(c)
    return out
