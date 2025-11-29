"""
Tests for the validation module.
"""

import pytest

from maverick_core.validation import (
    validate_currency_code,
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


class TestValidateSymbol:
    """Test symbol validation."""

    def test_valid_symbol(self):
        is_valid, error = validate_symbol("AAPL")
        assert is_valid is True
        assert error is None

    def test_empty_symbol(self):
        is_valid, error = validate_symbol("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_symbol_too_short(self):
        is_valid, error = validate_symbol("A", min_length=2)
        assert is_valid is False
        assert "at least 2 characters" in error

    def test_symbol_too_long(self):
        is_valid, error = validate_symbol("TOOLONGSYMBOL", max_length=10)
        assert is_valid is False
        assert "at most 10 characters" in error


class TestValidatePositiveNumber:
    """Test positive number validation."""

    def test_positive_number(self):
        is_valid, error = validate_positive_number(10)
        assert is_valid is True
        assert error is None

    def test_zero_not_allowed(self):
        is_valid, error = validate_positive_number(0)
        assert is_valid is False
        assert "must be positive" in error

    def test_zero_allowed(self):
        is_valid, error = validate_positive_number(0, allow_zero=True)
        assert is_valid is True
        assert error is None

    def test_negative_number(self):
        is_valid, error = validate_positive_number(-5)
        assert is_valid is False
        assert "must be positive" in error

    def test_negative_with_allow_zero(self):
        is_valid, error = validate_positive_number(-5, allow_zero=True)
        assert is_valid is False
        assert "must be non-negative" in error


class TestValidateInRange:
    """Test range validation."""

    def test_value_in_range(self):
        is_valid, error = validate_in_range(5, 1, 10)
        assert is_valid is True
        assert error is None

    def test_value_below_min(self):
        is_valid, error = validate_in_range(0, 1, 10)
        assert is_valid is False
        assert ">= 1" in error

    def test_value_above_max(self):
        is_valid, error = validate_in_range(15, 1, 10)
        assert is_valid is False
        assert "<= 10" in error

    def test_exclusive_range(self):
        is_valid, error = validate_in_range(1, 1, 10, inclusive=False)
        assert is_valid is False
        assert "> 1" in error


class TestValidateEmail:
    """Test email validation."""

    def test_valid_email(self):
        is_valid, error = validate_email("user@example.com")
        assert is_valid is True
        assert error is None

    def test_empty_email(self):
        is_valid, error = validate_email("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_invalid_email_no_at(self):
        is_valid, error = validate_email("userexample.com")
        assert is_valid is False
        assert "Invalid email format" in error

    def test_invalid_email_no_domain(self):
        is_valid, error = validate_email("user@")
        assert is_valid is False
        assert "Invalid email format" in error


class TestValidateUrl:
    """Test URL validation."""

    def test_valid_http_url(self):
        is_valid, error = validate_url("http://example.com")
        assert is_valid is True
        assert error is None

    def test_valid_https_url(self):
        is_valid, error = validate_url("https://example.com/path")
        assert is_valid is True
        assert error is None

    def test_empty_url(self):
        is_valid, error = validate_url("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_invalid_url(self):
        is_valid, error = validate_url("not-a-url")
        assert is_valid is False
        assert "Invalid URL format" in error

    def test_require_https(self):
        is_valid, error = validate_url("http://example.com", require_https=True)
        assert is_valid is False
        assert "Invalid HTTPS URL format" in error


class TestValidateNotEmpty:
    """Test not empty validation."""

    def test_non_empty_string(self):
        is_valid, error = validate_not_empty("test", "Field")
        assert is_valid is True
        assert error is None

    def test_empty_string(self):
        is_valid, error = validate_not_empty("", "Username")
        assert is_valid is False
        assert "Username cannot be empty" in error

    def test_whitespace_only(self):
        is_valid, error = validate_not_empty("   ", "Field")
        assert is_valid is False
        assert "cannot be empty" in error


class TestValidateMinLength:
    """Test minimum length validation."""

    def test_sufficient_length(self):
        is_valid, error = validate_min_length("hello", 3, "Password")
        assert is_valid is True
        assert error is None

    def test_insufficient_length(self):
        is_valid, error = validate_min_length("hi", 3, "Password")
        assert is_valid is False
        assert "Password must be at least 3 characters" in error


class TestValidateMaxLength:
    """Test maximum length validation."""

    def test_within_max(self):
        is_valid, error = validate_max_length("hello", 10, "Field")
        assert is_valid is True
        assert error is None

    def test_exceeds_max(self):
        is_valid, error = validate_max_length("hello world", 5, "Title")
        assert is_valid is False
        assert "Title must be at most 5 characters" in error


class TestValidateOneOf:
    """Test one-of validation."""

    def test_valid_value(self):
        is_valid, error = validate_one_of("USD", ["USD", "INR", "EUR"])
        assert is_valid is True
        assert error is None

    def test_invalid_value(self):
        is_valid, error = validate_one_of("GBP", ["USD", "INR", "EUR"])
        assert is_valid is False
        assert "must be one of: USD, INR, EUR" in error

    def test_case_insensitive(self):
        is_valid, error = validate_one_of("usd", ["USD", "INR"], case_sensitive=False)
        assert is_valid is True
        assert error is None


class TestValidatePercentage:
    """Test percentage validation."""

    def test_valid_percentage(self):
        is_valid, error = validate_percentage(50)
        assert is_valid is True
        assert error is None

    def test_percentage_zero(self):
        is_valid, error = validate_percentage(0)
        assert is_valid is True
        assert error is None

    def test_percentage_100(self):
        is_valid, error = validate_percentage(100)
        assert is_valid is True
        assert error is None

    def test_percentage_over_100(self):
        is_valid, error = validate_percentage(150)
        assert is_valid is False
        assert "between 0 and 100" in error

    def test_negative_percentage(self):
        is_valid, error = validate_percentage(-10)
        assert is_valid is False
        assert "between 0 and 100" in error

    def test_negative_allowed(self):
        is_valid, error = validate_percentage(-10, allow_negative=True)
        assert is_valid is True
        assert error is None


class TestValidateCurrencyCode:
    """Test currency code validation."""

    def test_valid_currency_code(self):
        is_valid, error = validate_currency_code("USD")
        assert is_valid is True
        assert error is None

    def test_empty_currency_code(self):
        is_valid, error = validate_currency_code("")
        assert is_valid is False
        assert "cannot be empty" in error

    def test_invalid_length(self):
        is_valid, error = validate_currency_code("US")
        assert is_valid is False
        assert "must be 3 letters" in error

    def test_lowercase_currency_code(self):
        is_valid, error = validate_currency_code("usd")
        assert is_valid is False
        assert "must be uppercase" in error

    def test_non_alpha_currency_code(self):
        is_valid, error = validate_currency_code("US1")
        assert is_valid is False
        assert "must contain only letters" in error

