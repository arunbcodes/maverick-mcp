"""
Audit logging module.

Provides audit logging for capability executions.
Supports compliance, debugging, and analytics.
"""

from maverick_capabilities.audit.protocols import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
)
from maverick_capabilities.audit.db_logger import DatabaseAuditLogger
from maverick_capabilities.audit.memory_logger import MemoryAuditLogger
from maverick_capabilities.audit.factory import (
    get_audit_logger,
    set_audit_logger,
    reset_audit_logger,
)

__all__ = [
    # Protocols
    "AuditLogger",
    "AuditEvent",
    "AuditEventType",
    # Implementations
    "DatabaseAuditLogger",
    "MemoryAuditLogger",
    # Factory
    "get_audit_logger",
    "set_audit_logger",
    "reset_audit_logger",
]
