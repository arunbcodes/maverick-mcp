"""
Maverick Core Validation Module.

This module provides input validation utilities, pydantic base models,
and common validators for use across all Maverick packages.
"""

from maverick_core.validation.base import (
    BaseRequest,
    BaseResponse,
    DateRangeMixin,
    DateString,
    DateValidator,
    PaginationMixin,
    Percentage,
    PositiveFloat,
    PositiveInt,
    StrictBaseModel,
    TickerSymbol,
    TickerValidator,
)
from maverick_core.validation.validators import (
    validate_currency_code,
    validate_date_range,
    validate_email,
    validate_in_range,
    validate_max_length,
    validate_min_length,
    validate_not_empty,
    validate_one_of,
    validate_percentage,
    validate_positive_number,
    validate_symbol,
    validate_url,
)

__all__ = [
    # Type annotations
    "TickerSymbol",
    "DateString",
    "PositiveInt",
    "PositiveFloat",
    "Percentage",
    # Base models
    "StrictBaseModel",
    "BaseRequest",
    "BaseResponse",
    # Mixins
    "PaginationMixin",
    "DateRangeMixin",
    # Validator classes
    "TickerValidator",
    "DateValidator",
    # Utility functions
    "validate_symbol",
    "validate_date_range",
    "validate_positive_number",
    "validate_in_range",
    "validate_email",
    "validate_url",
    "validate_not_empty",
    "validate_min_length",
    "validate_max_length",
    "validate_one_of",
    "validate_percentage",
    "validate_currency_code",
]

