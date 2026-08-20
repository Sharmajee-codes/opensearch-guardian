"""Core type definitions shared across guardian packages."""

from .auth_models import (
    BasicCredentials,
    ClientCertCredentials,
    Credentials,
)
from .connection_models import (
    AuthMethod,
    ConnectionMode,
    ConnectionProfile,
    ConnectionStatus,
    ConnectionTestResult,
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