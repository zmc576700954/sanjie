"""DocHub-specific errors."""

from __future__ import annotations

from core.shared.errors import ComponentError


class DocHubError(ComponentError):
    """Base error for DocHub operations."""


class DocumentNotFoundError(DocHubError):
    """Raised when a requested document is not found."""


class AddendumNotFoundError(DocHubError):
    """Raised when a requested addendum is not found."""


class DuplicateDocumentError(DocHubError):
    """Raised when creating a document with an existing doc_id."""


class InvalidDocumentTypeError(DocHubError):
    """Raised when a document type is not a valid Diátaxis type."""
