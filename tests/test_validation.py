"""Unit tests for validation.py - input sanitization and crash-proofing."""

import unittest
from unittest.mock import patch

from validation import (
    prompt_age,
    prompt_baggage_weight,
    prompt_float,
    prompt_int,
    prompt_menu_choice,
    prompt_optional_text,
    prompt_passenger_name,
)


class TestValidationHelpers(unittest.TestCase):
    """Test suite verifying interactive input functions with mocked stdin."""

    # ---------------------------------------------------------
    # Integer Validation Tests
    # ---------------------------------------------------------
    @patch("builtins.input", side_effect=["42"])
    def test_prompt_int_valid_single_attempt(self, mock_input):
        """Valid integer returns immediately."""
        result = prompt_int("Enter number: ")
        self.assertEqual(result, 42)
        self.assertEqual(mock_input.call_count, 1)

    @patch("builtins.input", side_effect=["abc", "", "   ", "12.34", "15"])
    def test_prompt_int_recovers_from_invalid_strings_and_blanks(self, mock_input):
        """Non-integer strings, empty lines, and floats re-prompt until integer received."""
        result = prompt_int("Enter number: ")
        self.assertEqual(result, 15)
        self.assertEqual(mock_input.call_count, 5)

    @patch("builtins.input", side_effect=["0", "25", "10"])
    def test_prompt_int_inclusive_bounds(self, mock_input):
        """Values below min or above max are rejected until in-range value provided."""
        result = prompt_int("Enter number (1-20): ", min_val=1, max_val=20)
        self.assertEqual(result, 10)
        self.assertEqual(mock_input.call_count, 3)

    # ---------------------------------------------------------
    # Floating-Point Validation Tests
    # ---------------------------------------------------------
    @patch("builtins.input", side_effect=["18.75"])
    def test_prompt_float_valid(self, mock_input):
        """Valid decimal returns float."""
        result = prompt_float("Enter weight: ")
        self.assertAlmostEqual(result, 18.75)
        self.assertEqual(mock_input.call_count, 1)

    @patch("builtins.input", side_effect=["nan", "NaN", "NAN", "inf", "-inf", "+infinity", "23.5"])
    def test_prompt_float_rejects_nan_and_infinities(self, mock_input):
        """NaN, Inf, and -Inf must be rejected and re-prompted."""
        result = prompt_float("Enter weight: ")
        self.assertAlmostEqual(result, 23.5)
        self.assertEqual(mock_input.call_count, 7)

    @patch("builtins.input", side_effect=["invalid", "", "   ", "12.8"])
    def test_prompt_float_recovers_from_invalid_strings(self, mock_input):
        """Non-numeric strings and empty lines re-prompt."""
        result = prompt_float("Enter float: ")
        self.assertAlmostEqual(result, 12.8)
        self.assertEqual(mock_input.call_count, 4)

    @patch("builtins.input", side_effect=["-5.0", "150.0", "50.5"])
    def test_prompt_float_bounds(self, mock_input):
        """Float bounds [0.0, 100.0] enforce limits properly."""
        result = prompt_float("Enter float: ", min_val=0.0, max_val=100.0)
        self.assertAlmostEqual(result, 50.5)
        self.assertEqual(mock_input.call_count, 3)

    # ---------------------------------------------------------
    # Baggage Weight Specific Tests
    # ---------------------------------------------------------
    @patch("builtins.input", side_effect=["0", "-1", "-0.01", "0.0", "22.5"])
    def test_prompt_baggage_weight_rejects_non_positive_and_zero(self, mock_input):
        """Zero and negative baggage weights must be rejected until strictly positive."""
        weight = prompt_baggage_weight()
        self.assertAlmostEqual(weight, 22.5)
        self.assertEqual(mock_input.call_count, 5)

    @patch("builtins.input", side_effect=["300.0", "35.0"])
    def test_prompt_baggage_weight_respects_max_val(self, mock_input):
        """Baggage weight exceeding maximum permitted capacity is rejected."""
        weight = prompt_baggage_weight(max_val=200.0)
        self.assertAlmostEqual(weight, 35.0)
        self.assertEqual(mock_input.call_count, 2)

    # ---------------------------------------------------------
    # Age Validation Specific Tests
    # ---------------------------------------------------------
    @patch("builtins.input", side_effect=["0", "-5", "121", "200", "28"])
    def test_prompt_age_out_of_range(self, mock_input):
        """Ages outside 1-120 are rejected."""
        age = prompt_age()
        self.assertEqual(age, 28)
        self.assertEqual(mock_input.call_count, 5)

    @patch("builtins.input", side_effect=["1"])
    def test_prompt_age_boundary_1(self, mock_input):
        """Age 1 (minimum bound) is accepted."""
        self.assertEqual(prompt_age(), 1)

    @patch("builtins.input", side_effect=["60"])
    def test_prompt_age_boundary_60(self, mock_input):
        """Age 60 (senior boundary non-discount) is accepted."""
        self.assertEqual(prompt_age(), 60)

    @patch("builtins.input", side_effect=["61"])
    def test_prompt_age_boundary_61(self, mock_input):
        """Age 61 (senior discount threshold) is accepted."""
        self.assertEqual(prompt_age(), 61)

    @patch("builtins.input", side_effect=["120"])
    def test_prompt_age_boundary_120(self, mock_input):
        """Age 120 (maximum bound) is accepted."""
        self.assertEqual(prompt_age(), 120)

    # ---------------------------------------------------------
    # Passenger Name Validation Tests
    # ---------------------------------------------------------
    @patch("builtins.input", side_effect=["", "   ", "\t", "  \n  ", "John Doe  "])
    def test_prompt_passenger_name_rejects_empty_and_whitespace(self, mock_input):
        """Blank or whitespace-only names are rejected and valid name is trimmed."""
        name = prompt_passenger_name()
        self.assertEqual(name, "John Doe")
        self.assertEqual(mock_input.call_count, 5)

    # ---------------------------------------------------------
    # Menu Selection Tests
    # ---------------------------------------------------------
    @patch("builtins.input", side_effect=["4", "99", "abc", "", "2"])
    def test_prompt_menu_choice_numeric_options(self, mock_input):
        """Out-of-range menu selections, empty inputs, and letters are rejected."""
        choice = prompt_menu_choice("Choose (1-3): ", ["1", "2", "3"])
        self.assertEqual(choice, "2")
        self.assertEqual(mock_input.call_count, 5)

    @patch("builtins.input", side_effect=["express"])
    def test_prompt_menu_choice_case_insensitive_match(self, mock_input):
        """Menu selection matches case-insensitively and returns canonical option."""
        choice = prompt_menu_choice("Choose: ", ["Superfast", "Express", "Fast Passenger"])
        self.assertEqual(choice, "Express")

    # ---------------------------------------------------------
    # Optional Text (Promo Code) Tests
    # ---------------------------------------------------------
    @patch("builtins.input", side_effect=["   "])
    def test_prompt_optional_text_blank_returns_none(self, mock_input):
        """Blank entry for optional input returns None."""
        self.assertIsNone(prompt_optional_text("Promo code: "))

    @patch("builtins.input", side_effect=["  ADG20  "])
    def test_prompt_optional_text_value_trimmed(self, mock_input):
        """Non-empty entry for optional input is stripped and returned."""
        self.assertEqual(prompt_optional_text("Promo code: "), "ADG20")


if __name__ == "__main__":
    unittest.main()
