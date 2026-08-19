"""Core type definitions shared across guardian packages."""

from .connection_models import (
    AuthMethod,
    ConnectionMode,
    ConnectionProfile,
    ConnectionStatus,
    ConnectionTestResult,
)
from .auth_models import (
    BasicCredentials,
    ClientCertCredentials,
    Credentials,
)

__all__ = [
    # connection_models
    "AuthMethod",
    "ConnectionMode",
    "ConnectionProfile",
    "ConnectionStatus",
    "ConnectionTestResult",
    # auth_models
    "BasicCredentials",
    "ClientCertCredentials",
    "Credentials",
]