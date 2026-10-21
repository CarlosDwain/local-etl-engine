"""Exception hierarchy. Expected outcomes are returned as results; these are for the unexpected."""


class EtlError(Exception):
    """Base class for every error this project raises on purpose."""


class ConfigError(EtlError):
    """The runtime configuration is missing or invalid."""


class ContractError(EtlError):
    """A data source contract is malformed or inconsistent."""


class IngestError(EtlError):
    """A source file could not be ingested at all (file-level failure)."""


class QualityGateError(EtlError):
    """A data quality gate failed and the run must stop."""
