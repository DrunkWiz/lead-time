"""A deliberately small JSON-schema subset, enough to validate model output.

Supported keywords: type, enum, required, properties, additionalProperties
(false only), items, values (for free-keyed objects), minItems, maxItems,
maxLength, pattern. Validation fails closed: anything unexpected raises.
"""
import re

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
}


class SchemaError(ValueError):
    pass


def validate(value, schema, path="$"):
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaError(f"{path}: {value!r} not in {schema['enum']}")
    t = schema.get("type")
    if t and not isinstance(value, _TYPES[t]):
        raise SchemaError(f"{path}: expected {t}, got {type(value).__name__}")
    if isinstance(value, str):
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            raise SchemaError(f"{path}: longer than {schema['maxLength']}")
        if "minLength" in schema and len(value.strip()) < schema["minLength"]:
            raise SchemaError(f"{path}: shorter than {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            raise SchemaError(f"{path}: does not match {schema['pattern']}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise SchemaError(f"{path}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise SchemaError(f"{path}: more than {schema['maxItems']} items")
        if "items" in schema:
            for i, v in enumerate(value):
                validate(v, schema["items"], f"{path}[{i}]")
    if isinstance(value, dict):
        for k in schema.get("required", []):
            if k not in value:
                raise SchemaError(f"{path}: missing {k}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(props)
            if extra:
                raise SchemaError(f"{path}: unexpected keys {sorted(extra)}")
        for k, v in value.items():
            if k in props:
                validate(v, props[k], f"{path}.{k}")
            elif "values" in schema:
                validate(v, schema["values"], f"{path}.{k}")
    return value
