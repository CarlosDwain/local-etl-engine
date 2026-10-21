"""Data layers (medallion naming noted for the team)."""

from enum import StrEnum


class Layer(StrEnum):
    RAW = "raw"  # bronze
    STAGING = "staging"  # silver
    MARTS = "marts"  # gold
