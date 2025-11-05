import pytest
from unittest.mock import patch, MagicMock
from tools.multiply import _multiply_numbers_impl as multiply_numbers


class TestMultiplyNumbers:
    """Test suite for multiply_numbers tool."""

    def test_multiply_positive_numbers(self):
        """Test multiplying two positive numbers."""
        result = multiply_numbers(5.0, 3.0)
        assert result == 15.0

    def test_multiply_negative_numbers(self):
        """Test multiplying two negative numbers."""
        result = multiply_numbers(-5.0, -3.0)
        assert result == 15.0

    def test_multiply_positive_and_negative(self):
        """Test multiplying a positive and negative number."""
        result = multiply_numbers(5.0, -3.0)
        assert result == -15.0

    def test_multiply_by_zero(self):
        """Test multiplying by zero."""
        result = multiply_numbers(5.0, 0.0)
        assert result == 0.0

    def test_multiply_decimals(self):
        """Test multiplying decimal numbers."""
        result = multiply_numbers(2.5, 4.0)
        assert result == 10.0

    def test_multiply_small_decimals(self):
        """Test multiplying small decimal numbers."""
        result = multiply_numbers(0.1, 0.2)
        assert result == pytest.approx(0.02)

    @patch('tools.multiply.span')
    def test_multiply_calls_span(self, mock_span):
        """Test that the span context manager is called."""
        mock_span.return_value.__enter__ = MagicMock()
        mock_span.return_value.__exit__ = MagicMock(return_value=False)
        
        multiply_numbers(2.0, 3.0)
        
        # Verify span was called with correct parameters
        mock_span.assert_called_once_with("multiply_numbers", "Multiplying two numbers")

    def test_multiply_large_numbers(self):
        """Test multiplying large numbers."""
        result = multiply_numbers(1000000.0, 1000000.0)
        assert result == 1000000000000.0

