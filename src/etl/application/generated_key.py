"""Generate stable business keys from meaningful row values."""

import hashlib
from collections.abc import Mapping, Sequence


def generated_key(row: Mapping[str, str | None], occurrence: int) -> str:
    meaningful = _meaningful_values(row)
    material = "|".join((*meaningful, str(occurrence)))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def generated_keys(rows: Sequence[Mapping[str, str | None]]) -> list[str]:
    occurrence_by_material: dict[str, int] = {}
    keys: list[str] = []
    for row in rows:
        material = "|".join(_meaningful_values(row))
        occurrence = occurrence_by_material.get(material, 0)
        occurrence_by_material[material] = occurrence + 1
        keys.append(generated_key(row, occurrence))
    return keys


def _meaningful_values(row: Mapping[str, str | None]) -> list[str]:
    return ["" if row[key] is None else str(row[key]) for key in sorted(row)]
