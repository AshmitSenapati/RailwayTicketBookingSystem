"""Unit tests for fare.py - 6-step calculation engine and promo system."""

from decimal import Decimal
import unittest

from fare import (
    PassengerFareBreakdown,
    apply_promo_code,
    calculate_passenger_fare,
    calculate_step1_slab_fare,
    calculate_step2_senior_discount,
    calculate_step3_train_premium,
    calculate_step4_class_premium,
    calculate_step5_baggage_fee,
    calculate_step6_flat_surcharge,
    calculate_subtotal,
    round_currency,
)


class TestFareCalculationSteps(unittest.TestCase):
    """Test suite covering the 6 calculation steps, boundary conditions, and reference case."""

    # ---------------------------------------------------------
    # Step 1: Slab Fare Tests
    # ---------------------------------------------------------
    def test_step1_slab_below_100km(self):
        """Distance < 100 km: Base INR 100 + dist * 1.00."""
        # 50 km -> 100 + 50*1.0 = 150.00
        self.assertEqual(calculate_step1_slab_fare(50), Decimal("150.00"))

    def test_step1_slab_exactly_100km(self):
        """Distance == 100 km: Base INR 100 + 100*1.0 = 200.00."""
        self.assertEqual(calculate_step1_slab_fare(100), Decimal("200.00"))

    def test_step1_slab_between_100_and_300km(self):
        """100 < Distance <= 300 km: Base 100 + 100*1.0 + (dist - 100)*0.80."""
        # 200 km -> 100 + 100 + 100*0.80 = 280.00
        self.assertEqual(calculate_step1_slab_fare(200), Decimal("280.00"))
        # 250 km -> 100 + 100 + 150*0.80 = 320.00
        self.assertEqual(calculate_step1_slab_fare(250), Decimal("320.00"))

    def test_step1_slab_exactly_300km(self):
        """Distance == 300 km: Base 100 + 100*1.0 + 200*0.80 = 360.00."""
        self.assertEqual(calculate_step1_slab_fare(300), Decimal("360.00"))

    def test_step1_slab_above_300km(self):
        """Distance > 300 km: Base 100 + 100*1.0 + 200*0.80 + (dist - 300)*0.60."""
        # 500 km -> 100 + 100 + 160 + 200*0.60 = 480.00
        self.assertEqual(calculate_step1_slab_fare(500), Decimal("480.00"))

    def test_step1_slab_reference_route_1460km(self):
        """Reference case: 1,460 km New Delhi - Mumbai slab fare must be exactly INR 1,056.00."""
        # 100 + 100*1.0 + 200*0.80 + 1160*0.60 = 100 + 100 + 160 + 696 = 1056.00
        self.assertEqual(calculate_step1_slab_fare(1460), Decimal("1056.00"))

    def test_step1_negative_distance_raises_error(self):
        """Negative distance must raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_step1_slab_fare(-10)

    # ---------------------------------------------------------
    # Step 2: Senior Citizen Discount Tests
    # ---------------------------------------------------------
    def test_step2_senior_citizen_boundary_age_60(self):
        """Age == 60: strictly NOT above 60, so NO discount applies."""
        fare, discount, applied = calculate_step2_senior_discount(Decimal("1000.00"), 60)
        self.assertEqual(fare, Decimal("1000.00"))
        self.assertEqual(discount, Decimal("0.00"))
        self.assertFalse(applied)

    def test_step2_senior_citizen_boundary_age_61(self):
        """Age == 61: strictly above 60, so 40% discount must apply."""
        fare, discount, applied = calculate_step2_senior_discount(Decimal("1000.00"), 61)
        self.assertEqual(discount, Decimal("400.00"))
        self.assertEqual(fare, Decimal("600.00"))
        self.assertTrue(applied)

    def test_step2_young_passenger(self):
        """Young passenger (age 25) gets no discount."""
        fare, discount, applied = calculate_step2_senior_discount(Decimal("1056.00"), 25)
        self.assertEqual(fare, Decimal("1056.00"))
        self.assertEqual(discount, Decimal("0.00"))
        self.assertFalse(applied)

    def test_step2_invalid_age_raises_error(self):
        """Age <= 0 must raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_step2_senior_discount(Decimal("1000.00"), 0)
        with self.assertRaises(ValueError):
            calculate_step2_senior_discount(Decimal("1000.00"), -5)

    # ---------------------------------------------------------
    # Step 3: Train Premium Tests
    # ---------------------------------------------------------
    def test_step3_train_premiums(self):
        """Verify train premium multipliers: Fast Passenger (1.0x), Express (1.25x), Superfast (1.50x)."""
        base = Decimal("1000.00")
        fare_fast, mult_fast = calculate_step3_train_premium(base, "Fast Passenger")
        self.assertEqual(fare_fast, Decimal("1000.00"))
        self.assertEqual(mult_fast, Decimal("1.00"))

        fare_exp, mult_exp = calculate_step3_train_premium(base, "Express")
        self.assertEqual(fare_exp, Decimal("1250.00"))
        self.assertEqual(mult_exp, Decimal("1.25"))

        fare_sup, mult_sup = calculate_step3_train_premium(base, "Superfast")
        self.assertEqual(fare_sup, Decimal("1500.00"))
        self.assertEqual(mult_sup, Decimal("1.50"))

    # ---------------------------------------------------------
    # Step 4: Class Premium Tests
    # ---------------------------------------------------------
    def test_step4_class_premiums(self):
        """Verify travel class multipliers: Sleeper (1.0x), AC 3-Tier (1.5x), AC 2-Tier (2.0x)."""
        base = Decimal("1000.00")
        fare_sl, mult_sl = calculate_step4_class_premium(base, "Sleeper")
        self.assertEqual(fare_sl, Decimal("1000.00"))
        self.assertEqual(mult_sl, Decimal("1.0"))

        fare_ac3, mult_ac3 = calculate_step4_class_premium(base, "AC 3-Tier")
        self.assertEqual(fare_ac3, Decimal("1500.00"))
        self.assertEqual(mult_ac3, Decimal("1.5"))

        fare_ac2, mult_ac2 = calculate_step4_class_premium(base, "AC 2-Tier")
        self.assertEqual(fare_ac2, Decimal("2000.00"))
        self.assertEqual(mult_ac2, Decimal("2.0"))

    # ---------------------------------------------------------
    # Step 5: Excess Baggage Fee Tests (Option A Pro-Rata)
    # ---------------------------------------------------------
    def test_step5_baggage_within_and_at_allowance(self):
        """Baggage <= allowance incurs zero fee."""
        # Sleeper: allowance is 20 kg
        fare1, excess1, fee1 = calculate_step5_baggage_fee(Decimal("1000.00"), "Sleeper", 15)
        self.assertEqual(excess1, Decimal("0.00"))
        self.assertEqual(fee1, Decimal("0.00"))
        self.assertEqual(fare1, Decimal("1000.00"))

        # Exactly at allowance: 20 kg
        fare2, excess2, fee2 = calculate_step5_baggage_fee(Decimal("1000.00"), "Sleeper", 20)
        self.assertEqual(excess2, Decimal("0.00"))
        self.assertEqual(fee2, Decimal("0.00"))
        self.assertEqual(fare2, Decimal("1000.00"))

    def test_step5_baggage_above_allowance_whole_kg(self):
        """Baggage > allowance incurs INR 15 per extra kg."""
        # AC 3-Tier: allowance is 30 kg, baggage is 35 kg -> 5 kg excess * 15 = INR 75.00
        fare, excess, fee = calculate_step5_baggage_fee(Decimal("1000.00"), "AC 3-Tier", 35)
        self.assertEqual(excess, Decimal("5.00"))
        self.assertEqual(fee, Decimal("75.00"))
        self.assertEqual(fare, Decimal("1075.00"))

    def test_step5_fractional_excess_baggage_option_a(self):
        """Option A: Proportional charging for fractional excess baggage."""
        # Sleeper (20 kg allowance), 25.5 kg -> 5.5 kg excess * 15 = INR 82.50
        fare, excess, fee = calculate_step5_baggage_fee(Decimal("1000.00"), "Sleeper", 25.5)
        self.assertEqual(excess, Decimal("5.50"))
        self.assertEqual(fee, Decimal("82.50"))
        self.assertEqual(fare, Decimal("1082.50"))

        # AC 2-Tier (40 kg allowance), 42.25 kg -> 2.25 kg excess * 15 = INR 33.75
        fare2, excess2, fee2 = calculate_step5_baggage_fee(Decimal("1000.00"), "AC 2-Tier", 42.25)
        self.assertEqual(excess2, Decimal("2.25"))
        self.assertEqual(fee2, Decimal("33.75"))
        self.assertEqual(fare2, Decimal("1033.75"))

    def test_step5_non_positive_baggage_raises_error(self):
        """Baggage weight <= 0 must raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_step5_baggage_fee(Decimal("1000.00"), "Sleeper", 0)
        with self.assertRaises(ValueError):
            calculate_step5_baggage_fee(Decimal("1000.00"), "Sleeper", -10)

    # ---------------------------------------------------------
    # Step 6: Flat Train Surcharge Tests
    # ---------------------------------------------------------
    def test_step6_train_surcharges(self):
        """Verify flat train surcharge: Superfast (+100), Express (+50), Fast Passenger (+0)."""
        base = Decimal("1000.00")
        fare_sup, sur_sup = calculate_step6_flat_surcharge(base, "Superfast")
        self.assertEqual(fare_sup, Decimal("1100.00"))
        self.assertEqual(sur_sup, Decimal("100.00"))

        fare_exp, sur_exp = calculate_step6_flat_surcharge(base, "Express")
        self.assertEqual(fare_exp, Decimal("1050.00"))
        self.assertEqual(sur_exp, Decimal("50.00"))

        fare_fast, sur_fast = calculate_step6_flat_surcharge(base, "Fast Passenger")
        self.assertEqual(fare_fast, Decimal("1000.00"))
        self.assertEqual(sur_fast, Decimal("0.00"))

    # ---------------------------------------------------------
    # Full 6-Step Pipeline & Assignment Reference Case
    # ---------------------------------------------------------
    def test_assignment_reference_case_step_by_step(self):
        """Verify the exact reference case from the assignment specification:

        Route: New Delhi - Mumbai (1,460 km)
        Train: Superfast
        Class: AC 3-Tier
        Age: 65 (Senior Citizen)
        Baggage: 35 kg

        Expected values:
        Step 1: INR 1,056.00
        Step 2: INR 633.60
        Step 3: INR 950.40
        Step 4: INR 1,425.60
        Step 5: INR 1,500.60
        Step 6: INR 1,600.60
        """
        breakdown = calculate_passenger_fare(
            passenger_name="Ashok Kumar",
            age=65,
            baggage_weight_kg=35,
            distance_km=1460,
            train_type="Superfast",
            travel_class="AC 3-Tier",
        )

        self.assertEqual(breakdown.step1_slab_fare, Decimal("1056.00"))
        self.assertEqual(breakdown.step2_senior_fare, Decimal("633.60"))
        self.assertTrue(breakdown.step2_discount_applied)
        self.assertEqual(breakdown.step2_discount_amount, Decimal("422.40"))
        self.assertEqual(breakdown.step3_train_fare, Decimal("950.40"))
        self.assertEqual(breakdown.step4_class_fare, Decimal("1425.60"))
        self.assertEqual(breakdown.step5_excess_kg, Decimal("5.00"))
        self.assertEqual(breakdown.step5_baggage_fee, Decimal("75.00"))
        self.assertEqual(breakdown.step5_baggage_fare, Decimal("1500.60"))
        self.assertEqual(breakdown.step6_surcharge, Decimal("100.00"))
        self.assertEqual(breakdown.step6_final_fare, Decimal("1600.60"))

    def test_passenger_fare_invalid_name_raises_error(self):
        """Blank or whitespace-only name must raise ValueError."""
        with self.assertRaises(ValueError):
            calculate_passenger_fare(
                passenger_name="   ",
                age=30,
                baggage_weight_kg=15,
                distance_km=500,
                train_type="Express",
                travel_class="Sleeper",
            )


class TestPromoCodeSystem(unittest.TestCase):
    """Test suite covering ADG20, WINTER500, case-insensitivity, and zero-floor rules."""

    def test_promo_adg20_standard(self):
        """ADG20 deducts flat 20% off subtotal."""
        res = apply_promo_code(Decimal("1000.00"), "ADG20")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.code_applied, "ADG20")
        self.assertEqual(res.discount_amount, Decimal("200.00"))
        self.assertEqual(res.final_total, Decimal("800.00"))

    def test_promo_adg20_case_insensitive_and_whitespace(self):
        """ADG20 matching is case-insensitive and trims whitespace."""
        res = apply_promo_code(Decimal("2500.00"), "  adg20  ")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.code_applied, "ADG20")
        self.assertEqual(res.discount_amount, Decimal("500.00"))
        self.assertEqual(res.final_total, Decimal("2000.00"))

    def test_promo_winter500_standard(self):
        """WINTER500 deducts flat INR 500 off subtotal."""
        res = apply_promo_code(Decimal("1600.60"), "WINTER500")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.code_applied, "WINTER500")
        self.assertEqual(res.discount_amount, Decimal("500.00"))
        self.assertEqual(res.final_total, Decimal("1100.60"))

    def test_promo_winter500_zero_floor(self):
        """WINTER500 on subtotal < INR 500 must not drop final total below zero."""
        # Subtotal INR 300 -> discount clamped to 300, final total = 0.00
        res = apply_promo_code(Decimal("300.00"), "winter500")
        self.assertTrue(res.is_valid)
        self.assertEqual(res.code_applied, "WINTER500")
        self.assertEqual(res.discount_amount, Decimal("300.00"))
        self.assertEqual(res.final_total, Decimal("0.00"))

    def test_promo_blank_or_none(self):
        """Empty or None promo code results in no discount and valid status."""
        for code in [None, "", "   "]:
            res = apply_promo_code(Decimal("1200.00"), code)
            self.assertTrue(res.is_valid)
            self.assertIsNone(res.code_applied)
            self.assertEqual(res.discount_amount, Decimal("0.00"))
            self.assertEqual(res.final_total, Decimal("1200.00"))

    def test_promo_invalid_code(self):
        """Unrecognized code results in no discount and is_valid=False."""
        res = apply_promo_code(Decimal("1200.00"), "SUMMER50")
        self.assertFalse(res.is_valid)
        self.assertIsNone(res.code_applied)
        self.assertEqual(res.discount_amount, Decimal("0.00"))
        self.assertEqual(res.final_total, Decimal("1200.00"))
        self.assertIn("Invalid promo code", res.message)

    def test_calculate_subtotal_multiple_passengers(self):
        """Verify subtotal sums all passengers' Step 6 final fares."""
        p1 = calculate_passenger_fare("Alice", 25, 15, 1460, "Express", "Sleeper")
        p2 = calculate_passenger_fare("Bob", 65, 30, 1460, "Express", "Sleeper")
        subtotal = calculate_subtotal([p1, p2])
        self.assertEqual(subtotal, p1.step6_final_fare + p2.step6_final_fare)

    def test_calculate_subtotal_empty_list_raises_error(self):
        """Empty passenger list raises ValueError."""
        with self.assertRaises(ValueError):
            calculate_subtotal([])


if __name__ == "__main__":
    unittest.main()
