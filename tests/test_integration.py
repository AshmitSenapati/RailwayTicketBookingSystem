"""Integration tests for the complete end-to-end booking flow."""

from decimal import Decimal
import io
import unittest
from unittest.mock import patch

from fare import (
    apply_promo_code,
    calculate_passenger_fare,
    calculate_subtotal,
)
from main import run_booking_flow
import routes


class TestIntegrationBookingFlow(unittest.TestCase):
    """End-to-end integration tests simulating complete user bookings."""

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input")
    def test_complete_booking_reference_case_with_adg20(self, mock_input, mock_stdout):
        """Simulate single passenger booking matching the assignment reference case with ADG20.

        Inputs:
        - Origin: 1 (New Delhi)
        - Destination: 1 (Mumbai)
        - Train Type: 1 (Superfast)
        - Travel Class: 2 (AC 3-Tier)
        - Passengers: 1
        - Passenger 1 Name: Ashok Kumar
        - Passenger 1 Age: 65
        - Passenger 1 Baggage: 35
        - Promo Code: ADG20
        """
        mock_input.side_effect = [
            "1",            # Origin: New Delhi
            "1",            # Destination: Mumbai
            "1",            # Train: Superfast
            "2",            # Class: AC 3-Tier
            "1",            # 1 Passenger
            "Ashok Kumar",  # Name
            "65",           # Age
            "35",           # Baggage kg
            "ADG20",        # Promo code
        ]

        run_booking_flow()
        output = mock_stdout.getvalue()

        # Check journey details
        self.assertIn("New Delhi <-> Mumbai", output)
        self.assertIn("1,460 km", output)
        self.assertIn("Superfast", output)
        self.assertIn("AC 3-Tier", output)

        # Check passenger breakdown
        self.assertIn("Ashok Kumar", output)
        self.assertIn("INR 1600.60", output)

        # Check Subtotal and 20% discount:
        # Subtotal: 1600.60
        # ADG20 20% discount = 320.12
        # Final Total = 1280.48
        self.assertIn("1600.60", output)
        self.assertIn("320.12", output)
        self.assertIn("1280.48", output)
        self.assertIn("OFFICIAL BOOKING INVOICE", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input")
    def test_multi_passenger_booking_with_winter500(self, mock_input, mock_stdout):
        """Simulate multi-passenger booking with senior citizen and young passenger, applying WINTER500.

        Route: Mumbai ↔ Hyderabad (711 km)
        Train: Express (1.25x multiplier, +INR 50 surcharge, 110 km/h)
        Class: Sleeper (1.0x multiplier, 20 kg allowance)
        Passenger 1: Rajesh Sharma, Age: 68 (Senior -> 40% discount on Step 1), Baggage: 22 kg (2 kg excess)
        Passenger 2: Priya Sharma, Age: 24 (No discount), Baggage: 18 kg (0 excess)
        Promo: WINTER500 (INR 500 discount)
        """
        # Step 1 for 711 km:
        # 100 + 100*1.0 + 200*0.8 + 411*0.6 = 100 + 100 + 160 + 246.60 = 606.60
        # Passenger 1 (Age 68):
        # Step 2: 606.60 * 0.60 = 363.96
        # Step 3 (Express 1.25x): 363.96 * 1.25 = 454.95
        # Step 4 (Sleeper 1.0x): 454.95 * 1.0 = 454.95
        # Step 5 (2 kg excess @ 15): 454.95 + 30.00 = 484.95
        # Step 6 (Express +50): 484.95 + 50.00 = 534.95

        # Passenger 2 (Age 24):
        # Step 2: 606.60
        # Step 3 (Express 1.25x): 606.60 * 1.25 = 758.25
        # Step 4 (Sleeper 1.0x): 758.25
        # Step 5 (0 excess): 758.25
        # Step 6 (Express +50): 758.25 + 50.00 = 808.25

        # Subtotal: 534.95 + 808.25 = 1343.20
        # WINTER500: -500.00 -> Final: 843.20

        # Station indices:
        # Stations: 1: New Delhi, 2: Mumbai, 3: Kolkata, 4: Chennai, 5: Hyderabad
        # Select Mumbai: "2"
        # Reachable from Mumbai: 1: New Delhi, 2: Kolkata, 3: Chennai, 4: Hyderabad -> Select "4"
        # Train Types: 1: Superfast, 2: Express, 3: Fast Passenger -> Select "2"
        # Travel Classes: 1: Sleeper, 2: AC 3-Tier, 3: AC 2-Tier -> Select "1"

        mock_input.side_effect = [
            "2",              # Origin: Mumbai
            "4",              # Destination: Hyderabad
            "2",              # Train: Express
            "1",              # Class: Sleeper
            "2",              # 2 Passengers
            "Rajesh Sharma",  # P1 Name
            "68",             # P1 Age
            "22",             # P1 Baggage
            "Priya Sharma",   # P2 Name
            "24",             # P2 Age
            "18",             # P2 Baggage
            "winter500",      # Promo code (lowercase)
        ]

        run_booking_flow()
        output = mock_stdout.getvalue()

        self.assertIn("Mumbai <-> Hyderabad", output)
        self.assertIn("711 km", output)
        self.assertIn("Rajesh Sharma", output)
        self.assertIn("Priya Sharma", output)
        self.assertIn("INR 534.95", output)
        self.assertIn("INR 808.25", output)
        self.assertIn("1343.20", output)
        self.assertIn("500.00", output)
        self.assertIn("843.20", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input")
    def test_booking_with_invalid_promo_code_and_blank_recovery(self, mock_input, mock_stdout):
        """Simulate booking with invalid promo code."""
        mock_input.side_effect = [
            "1",            # Origin: New Delhi
            "2",            # Destination: Kolkata
            "3",            # Train: Fast Passenger
            "1",            # Class: Sleeper
            "1",            # 1 Passenger
            "Rahul",        # Name
            "30",           # Age
            "15",           # Baggage
            "INVALID_CODE", # Invalid promo code
        ]

        run_booking_flow()
        output = mock_stdout.getvalue()

        self.assertIn("Invalid promo code 'INVALID_CODE'", output)
        self.assertIn("Proceeding without discount", output)


if __name__ == "__main__":
    unittest.main()
