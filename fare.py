"""fare.py - 6-Step Fare Calculation Engine & Promotional Code System.

This module encapsulates all mathematical calculations for the ADG Railway Ticket
Booking System. It executes the exact six-step fare calculation sequence for each
individual passenger, aggregates booking subtotals, and applies promotional codes.

Design Rules:
- NO interactive code (no `input()` or `print()` calls).
- All financial values use Python's `Decimal` with standard `ROUND_HALF_UP` rounding.
- Fractional excess baggage weights are handled via Option A (proportional charging
  at INR 15.00 per excess kg, rounded to 2 decimal places).
- Leverages `routes.py` for all train and class specifications.
"""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple

from routes import get_class_specs, get_train_specs

# Monetary quantization to 2 decimal places
CENT = Decimal("0.01")

# Step 1 Constants
BASE_FARE = Decimal("100.00")
SLAB1_LIMIT = Decimal("100.00")
SLAB1_RATE = Decimal("1.00")
SLAB2_LIMIT = Decimal("300.00")
SLAB2_RATE = Decimal("0.80")
SLAB3_RATE = Decimal("0.60")

# Step 2 Constants
SENIOR_AGE_THRESHOLD = 60
SENIOR_DISCOUNT_PERCENT = Decimal("0.40")

# Step 5 Constants
# Option A interpretation: fractional excess kilograms charged proportionally at INR 15.00/kg
EXCESS_BAGGAGE_RATE_PER_KG = Decimal("15.00")

# Promo Code Definitions
PROMO_ADG20 = "ADG20"
PROMO_WINTER500 = "WINTER500"
SUPPORTED_PROMO_CODES = {PROMO_ADG20, PROMO_WINTER500}


def round_currency(amount: Decimal) -> Decimal:
    """Quantize a Decimal amount to two decimal places using standard ROUND_HALF_UP."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class PassengerFareBreakdown:
    """Structured breakdown of all six calculation steps for an individual passenger."""

    passenger_name: str
    age: int
    baggage_weight_kg: Decimal
    distance_km: Decimal
    train_type: str
    travel_class: str

    step1_slab_fare: Decimal
    step2_senior_fare: Decimal
    step2_discount_applied: bool
    step2_discount_amount: Decimal
    step3_train_fare: Decimal
    step3_multiplier: Decimal
    step4_class_fare: Decimal
    step4_multiplier: Decimal
    step5_baggage_fare: Decimal
    step5_excess_kg: Decimal
    step5_baggage_fee: Decimal
    step6_final_fare: Decimal
    step6_surcharge: Decimal

    def to_dict(self) -> Dict[str, object]:
        """Convert the breakdown to a plain dictionary for external consumption."""
        return {
            "passenger_name": self.passenger_name,
            "age": self.age,
            "baggage_weight_kg": float(self.baggage_weight_kg),
            "distance_km": float(self.distance_km),
            "train_type": self.train_type,
            "travel_class": self.travel_class,
            "step1_slab_fare": float(self.step1_slab_fare),
            "step2_senior_fare": float(self.step2_senior_fare),
            "step2_discount_applied": self.step2_discount_applied,
            "step2_discount_amount": float(self.step2_discount_amount),
            "step3_train_fare": float(self.step3_train_fare),
            "step3_multiplier": float(self.step3_multiplier),
            "step4_class_fare": float(self.step4_class_fare),
            "step4_multiplier": float(self.step4_multiplier),
            "step5_baggage_fare": float(self.step5_baggage_fare),
            "step5_excess_kg": float(self.step5_excess_kg),
            "step5_baggage_fee": float(self.step5_baggage_fee),
            "step6_final_fare": float(self.step6_final_fare),
            "step6_surcharge": float(self.step6_surcharge),
        }


@dataclass(frozen=True)
class PromoResult:
    """Outcome of attempting to apply a promotional code to a subtotal."""

    code_entered: Optional[str]
    code_applied: Optional[str]
    is_valid: bool
    discount_amount: Decimal
    final_total: Decimal
    message: str


def calculate_step1_slab_fare(distance_km: float | int | Decimal) -> Decimal:
    """Step 1 - Slab Fare Calculation.

    Base fare = INR 100.
    - First 100 km: INR 1.00 per km
    - Next 200 km (101 to 300 km): INR 0.80 per km
    - Beyond 300 km: INR 0.60 per km

    Raises:
        ValueError: If distance is negative.
    """
    dist = Decimal(str(distance_km))
    if dist < Decimal("0"):
        raise ValueError(f"Distance cannot be negative, got {distance_km}.")

    fare = BASE_FARE
    if dist <= SLAB1_LIMIT:
        fare += dist * SLAB1_RATE
    elif dist <= SLAB2_LIMIT:
        fare += (SLAB1_LIMIT * SLAB1_RATE) + ((dist - SLAB1_LIMIT) * SLAB2_RATE)
    else:
        fare += (
            (SLAB1_LIMIT * SLAB1_RATE)
            + ((SLAB2_LIMIT - SLAB1_LIMIT) * SLAB2_RATE)
            + ((dist - SLAB2_LIMIT) * SLAB3_RATE)
        )

    return round_currency(fare)


def calculate_step2_senior_discount(
    step1_fare: Decimal, age: int
) -> Tuple[Decimal, Decimal, bool]:
    """Step 2 - Senior Citizen Discount.

    If age is strictly above 60 years (> 60), apply a 40% discount to Step 1.
    Age 60 or below receives no discount.

    Returns:
        tuple: (step2_fare, discount_amount, is_senior_discount_applied)

    Raises:
        ValueError: If age is non-positive or Step 1 fare is negative.
    """
    if age <= 0:
        raise ValueError(f"Age must be a positive integer, got {age}.")
    if step1_fare < Decimal("0"):
        raise ValueError(f"Step 1 fare cannot be negative, got {step1_fare}.")

    if age > SENIOR_AGE_THRESHOLD:
        discount = round_currency(step1_fare * SENIOR_DISCOUNT_PERCENT)
        step2_fare = step1_fare - discount
        return (step2_fare, discount, True)

    return (step1_fare, Decimal("0.00"), False)


def calculate_step3_train_premium(
    step2_fare: Decimal, train_type: str
) -> Tuple[Decimal, Decimal]:
    """Step 3 - Train Premium Multiplier.

    Multiplies Step 2 result by train premium:
    - Fast Passenger: 1.00x
    - Express: 1.25x
    - Superfast: 1.50x

    Returns:
        tuple: (step3_fare, multiplier)
    """
    if step2_fare < Decimal("0"):
        raise ValueError(f"Step 2 fare cannot be negative, got {step2_fare}.")

    specs = get_train_specs(train_type)
    multiplier = Decimal(str(specs["premium_multiplier"]))
    step3_fare = round_currency(step2_fare * multiplier)
    return (step3_fare, multiplier)


def calculate_step4_class_premium(
    step3_fare: Decimal, travel_class: str
) -> Tuple[Decimal, Decimal]:
    """Step 4 - Class Premium Multiplier.

    Multiplies Step 3 result by travel class multiplier:
    - Sleeper: 1.0x
    - AC 3-Tier: 1.5x
    - AC 2-Tier: 2.0x

    Returns:
        tuple: (step4_fare, multiplier)
    """
    if step3_fare < Decimal("0"):
        raise ValueError(f"Step 3 fare cannot be negative, got {step3_fare}.")

    specs = get_class_specs(travel_class)
    multiplier = Decimal(str(specs["multiplier"]))
    step4_fare = round_currency(step3_fare * multiplier)
    return (step4_fare, multiplier)


def calculate_step5_baggage_fee(
    step4_fare: Decimal, travel_class: str, baggage_weight_kg: float | int | Decimal
) -> Tuple[Decimal, Decimal, Decimal]:
    """Step 5 - Excess Baggage Fee.

    If baggage weight exceeds the free allowance for the travel class, add a penalty
    of INR 15 for every extra kilogram (Option A: proportional charging for fractional kg).

    Returns:
        tuple: (step5_fare, excess_kg, baggage_fee)

    Raises:
        ValueError: If baggage weight is <= 0 or Step 4 fare is negative.
    """
    baggage = Decimal(str(baggage_weight_kg))
    if baggage <= Decimal("0"):
        raise ValueError(
            f"Baggage weight must be strictly positive (> 0 kg), got {baggage_weight_kg}."
        )
    if step4_fare < Decimal("0"):
        raise ValueError(f"Step 4 fare cannot be negative, got {step4_fare}.")

    specs = get_class_specs(travel_class)
    allowance = Decimal(str(specs["free_baggage_kg"]))

    if baggage > allowance:
        excess_kg = baggage - allowance
        baggage_fee = round_currency(excess_kg * EXCESS_BAGGAGE_RATE_PER_KG)
    else:
        excess_kg = Decimal("0.00")
        baggage_fee = Decimal("0.00")

    step5_fare = step4_fare + baggage_fee
    return (step5_fare, excess_kg, baggage_fee)


def calculate_step6_flat_surcharge(
    step5_fare: Decimal, train_type: str
) -> Tuple[Decimal, Decimal]:
    """Step 6 - Flat Train Surcharge.

    Adds final flat surcharge per passenger based on train type:
    - Superfast: +INR 100
    - Express: +INR 50
    - Fast Passenger: +INR 0

    Returns:
        tuple: (step6_final_fare, surcharge)
    """
    if step5_fare < Decimal("0"):
        raise ValueError(f"Step 5 fare cannot be negative, got {step5_fare}.")

    specs = get_train_specs(train_type)
    surcharge = Decimal(str(specs["flat_surcharge"]))
    step6_final_fare = step5_fare + surcharge
    return (step6_final_fare, surcharge)


def calculate_passenger_fare(
    passenger_name: str,
    age: int,
    baggage_weight_kg: float | int | Decimal,
    distance_km: float | int | Decimal,
    train_type: str,
    travel_class: str,
) -> PassengerFareBreakdown:
    """Execute the exact six-step fare calculation sequence for an individual passenger.

    Returns a complete PassengerFareBreakdown containing intermediate and final fares.
    """
    name_clean = passenger_name.strip()
    if not name_clean:
        raise ValueError("Passenger name cannot be empty.")

    dist = Decimal(str(distance_km))
    baggage = Decimal(str(baggage_weight_kg))

    # Step 1: Slab Fare
    step1_fare = calculate_step1_slab_fare(dist)

    # Step 2: Senior Citizen Discount
    step2_fare, senior_discount, is_senior = calculate_step2_senior_discount(step1_fare, age)

    # Step 3: Train Premium
    step3_fare, train_mult = calculate_step3_train_premium(step2_fare, train_type)

    # Step 4: Class Premium
    step4_fare, class_mult = calculate_step4_class_premium(step3_fare, travel_class)

    # Step 5: Excess Baggage Fee
    step5_fare, excess_kg, baggage_fee = calculate_step5_baggage_fee(
        step4_fare, travel_class, baggage
    )

    # Step 6: Flat Surcharge
    step6_fare, surcharge = calculate_step6_flat_surcharge(step5_fare, train_type)

    return PassengerFareBreakdown(
        passenger_name=name_clean,
        age=age,
        baggage_weight_kg=baggage,
        distance_km=dist,
        train_type=train_type,
        travel_class=travel_class,
        step1_slab_fare=step1_fare,
        step2_senior_fare=step2_fare,
        step2_discount_applied=is_senior,
        step2_discount_amount=senior_discount,
        step3_train_fare=step3_fare,
        step3_multiplier=train_mult,
        step4_class_fare=step4_fare,
        step4_multiplier=class_mult,
        step5_baggage_fare=step5_fare,
        step5_excess_kg=excess_kg,
        step5_baggage_fee=baggage_fee,
        step6_final_fare=step6_fare,
        step6_surcharge=surcharge,
    )


def calculate_subtotal(passengers: List[PassengerFareBreakdown]) -> Decimal:
    """Sum the individual Step 6 final fares for all passengers to produce a Subtotal."""
    if not passengers:
        raise ValueError("Passenger list cannot be empty.")
    return sum((p.step6_final_fare for p in passengers), Decimal("0.00"))


def apply_promo_code(subtotal: Decimal, promo_code: Optional[str]) -> PromoResult:
    """Apply an optional promotional code to a booking subtotal.

    Supported Codes:
    - ADG20: Deducts a flat 20% off the subtotal.
    - WINTER500: Deducts a flat INR 500 off the subtotal. Final amount never drops below 0.

    Rules:
    - Case-insensitive matching.
    - Blank or None input results in no discount.
    - Invalid code results in no discount and an explicit invalid status.
    - At most one code may be applied per booking.
    """
    if subtotal < Decimal("0"):
        raise ValueError(f"Subtotal cannot be negative, got {subtotal}.")

    if promo_code is None or not promo_code.strip():
        return PromoResult(
            code_entered=None,
            code_applied=None,
            is_valid=True,
            discount_amount=Decimal("0.00"),
            final_total=subtotal,
            message="No promotional code applied.",
        )

    code_clean = promo_code.strip().upper()

    if code_clean == PROMO_ADG20:
        discount = round_currency(subtotal * Decimal("0.20"))
        final_total = max(Decimal("0.00"), subtotal - discount)
        return PromoResult(
            code_entered=promo_code.strip(),
            code_applied=PROMO_ADG20,
            is_valid=True,
            discount_amount=discount,
            final_total=final_total,
            message="Promotional code ADG20 applied: 20% discount on subtotal.",
        )

    if code_clean == PROMO_WINTER500:
        discount = min(subtotal, Decimal("500.00"))
        final_total = max(Decimal("0.00"), subtotal - Decimal("500.00"))
        return PromoResult(
            code_entered=promo_code.strip(),
            code_applied=PROMO_WINTER500,
            is_valid=True,
            discount_amount=discount,
            final_total=final_total,
            message="Promotional code WINTER500 applied: INR 500 discount on subtotal.",
        )

    # Invalid code handling
    return PromoResult(
        code_entered=promo_code.strip(),
        code_applied=None,
        is_valid=False,
        discount_amount=Decimal("0.00"),
        final_total=subtotal,
        message=f"Invalid promo code '{promo_code.strip()}'. Proceeding without discount.",
    )
