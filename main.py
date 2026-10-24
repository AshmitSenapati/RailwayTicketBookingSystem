"""main.py - Interactive CLI Coordinator for the Railway Ticket Booking System.

This module coordinates user interactions, input intake, module delegation, and invoice
presentation.

Architecture Rules:
- main.py serves strictly as an orchestrator and presentation layer.
- NO mathematical calculations or static route/train/class definitions reside here.
- All routing and train/class specifications are retrieved from routes.py.
- All fare calculations and promo logic are delegated to fare.py.
- All interactive inputs are validated through validation.py helpers.
"""

import sys
from decimal import Decimal
from typing import List, Tuple

import fare
import routes
import validation


def display_banner() -> None:
    """Print the application header banner."""
    print("\n" + "=" * 68)
    print("           ADG RAILWAY TICKET BOOKING SYSTEM")
    print("=" * 68)


def select_route() -> Tuple[str, str, int]:
    """Guide the user to select origin and destination stations.

    Returns:
        tuple: (origin_station, destination_station, distance_km)
    """
    stations = routes.get_stations()
    print("\n--- Step 1: Select Origin Station ---")
    for idx, station in enumerate(stations, start=1):
        print(f"  [{idx}] {station}")

    origin_choice = validation.prompt_menu_choice(
        prompt=f"Select Origin (1-{len(stations)}): ",
        valid_options=[str(i) for i in range(1, len(stations) + 1)],
    )
    origin = stations[int(origin_choice) - 1]

    destinations = routes.get_destinations(origin)
    print(f"\n--- Step 2: Select Destination (Reachable from {origin}) ---")
    for idx, dest in enumerate(destinations, start=1):
        print(f"  [{idx}] {dest}")

    dest_choice = validation.prompt_menu_choice(
        prompt=f"Select Destination (1-{len(destinations)}): ",
        valid_options=[str(i) for i in range(1, len(destinations) + 1)],
    )
    destination = destinations[int(dest_choice) - 1]

    distance_km = routes.get_distance(origin, destination)
    print(f"\n>> Selected Journey: {origin} <-> {destination} ({distance_km:,} km)")
    return origin, destination, distance_km


def select_train(distance_km: int) -> Tuple[str, str]:
    """Guide the user to select a train type and display estimated travel time.

    Returns:
        tuple: (train_type, travel_time_display_string)
    """
    train_names = list(routes.TRAIN_TYPES.keys())
    print("\n--- Step 3: Select Train Type ---")
    for idx, name in enumerate(train_names, start=1):
        specs = routes.get_train_specs(name)
        surcharge = specs["flat_surcharge"]
        print(
            f"  [{idx}] {name:<15} (Avg Speed: {specs['speed_kmh']} km/h, Surcharge: INR {surcharge:.2f})"
        )

    choice = validation.prompt_menu_choice(
        prompt=f"Select Train Type (1-{len(train_names)}): ",
        valid_options=[str(i) for i in range(1, len(train_names) + 1)],
    )
    train_type = train_names[int(choice) - 1]

    total_hours, hours, minutes = routes.calculate_travel_time(distance_km, train_type)
    time_display = f"{hours} hrs {minutes:02d} mins ({total_hours:.2f} hrs)"
    print(f">> Train Selected: {train_type} | Estimated Travel Time: {time_display}")
    return train_type, time_display


def select_travel_class() -> str:
    """Guide the user to select a travel class.

    Returns:
        str: Selected travel class name.
    """
    class_names = list(routes.TRAVEL_CLASSES.keys())
    print("\n--- Step 4: Select Travel Class ---")
    for idx, name in enumerate(class_names, start=1):
        specs = routes.get_class_specs(name)
        multiplier = specs["multiplier"]
        allowance = specs["free_baggage_kg"]
        print(
            f"  [{idx}] {name:<12} (Multiplier: {multiplier:.1f}x, Free Baggage Allowance: {allowance:.0f} kg)"
        )

    choice = validation.prompt_menu_choice(
        prompt=f"Select Travel Class (1-{len(class_names)}): ",
        valid_options=[str(i) for i in range(1, len(class_names) + 1)],
    )
    travel_class = class_names[int(choice) - 1]
    print(f">> Travel Class Selected: {travel_class}")
    return travel_class


def intake_passengers(
    distance_km: int, train_type: str, travel_class: str
) -> List[fare.PassengerFareBreakdown]:
    """Collect passenger details and compute individual 6-step fares.

    Returns:
        list of fare.PassengerFareBreakdown objects.
    """
    print("\n--- Step 5: Passenger Information ---")
    num_passengers = validation.prompt_int(
        prompt="Enter number of passengers (1-10): ",
        min_val=1,
        max_val=10,
    )

    passengers: List[fare.PassengerFareBreakdown] = []
    for i in range(1, num_passengers + 1):
        print(f"\n  [Passenger {i} of {num_passengers}]")
        name = validation.prompt_passenger_name("    Full Name: ")
        age = validation.prompt_age("    Age (1-120): ")
        baggage = validation.prompt_baggage_weight(
            "    Baggage Weight in kg (strictly positive): ", max_val=200.0
        )

        breakdown = fare.calculate_passenger_fare(
            passenger_name=name,
            age=age,
            baggage_weight_kg=baggage,
            distance_km=distance_km,
            train_type=train_type,
            travel_class=travel_class,
        )
        passengers.append(breakdown)

    return passengers


def apply_promotions(subtotal: Decimal) -> fare.PromoResult:
    """Prompt for an optional promo code and apply it via fare module."""
    print("\n--- Step 6: Promotional Code ---")
    print("Available codes: ADG20 (20% off) | WINTER500 (INR 500 off)")
    code_input = validation.prompt_optional_text(
        "Enter Promo Code (or press Enter to skip): "
    )
    result = fare.apply_promo_code(subtotal, code_input)

    if result.code_applied:
        print(f">> SUCCESS: {result.message}")
    elif not result.is_valid:
        print(f">> NOTICE: {result.message}")
    else:
        print(">> No promo code applied.")

    return result


def display_invoice(
    origin: str,
    destination: str,
    distance_km: int,
    train_type: str,
    travel_time_display: str,
    travel_class: str,
    passengers: List[fare.PassengerFareBreakdown],
    promo_result: fare.PromoResult,
) -> None:
    """Render a comprehensive, readable booking receipt."""
    subtotal = fare.calculate_subtotal(passengers)

    print("\n" + "=" * 68)
    print("                     OFFICIAL BOOKING INVOICE")
    print("=" * 68)
    print(f" Route:               {origin} <-> {destination}")
    print(f" Distance:            {distance_km:,} km")
    print(f" Train Type:          {train_type}")
    print(f" Estimated Time:      {travel_time_display}")
    print(f" Travel Class:        {travel_class}")
    print("-" * 68)
    print(" PASSENGER BREAKDOWN:")
    print(
        f" {'#':<3} {'Name':<18} {'Age':<5} {'Baggage':<10} {'Senior Disc':<13} {'Excess Fee':<12} {'Fare':>6}"
    )
    print("-" * 68)

    for idx, p in enumerate(passengers, start=1):
        senior_str = f"-INR {p.step2_discount_amount:.2f}" if p.step2_discount_applied else "None"
        excess_str = f"+INR {p.step5_baggage_fee:.2f}" if p.step5_excess_kg > Decimal("0") else "INR 0.00"
        print(
            f" {idx:<3} {p.passenger_name[:17]:<18} {p.age:<5} {p.baggage_weight_kg:.1f} kg    "
            f"{senior_str:<13} {excess_str:<12} INR {p.step6_final_fare:.2f}"
        )

    print("-" * 68)
    print(" STEP-BY-STEP AUDIT TRAIL (Per Passenger):")
    for idx, p in enumerate(passengers, start=1):
        print(f" Passenger {idx} ({p.passenger_name}):")
        print(f"   Step 1 (Base Slab Fare):         INR {p.step1_slab_fare:.2f}")
        print(
            f"   Step 2 (After Senior Citizen):   INR {p.step2_senior_fare:.2f} "
            f"({'-40%' if p.step2_discount_applied else 'No discount'})"
        )
        print(
            f"   Step 3 (Train Premium {p.step3_multiplier:.2f}x):     INR {p.step3_train_fare:.2f}"
        )
        print(
            f"   Step 4 (Class Multiplier {p.step4_multiplier:.1f}x):  INR {p.step4_class_fare:.2f}"
        )
        print(
            f"   Step 5 (Excess Baggage Fee):     INR {p.step5_baggage_fare:.2f} "
            f"(+{p.step5_excess_kg:.2f} kg excess)"
        )
        print(
            f"   Step 6 (Train Flat Surcharge):   INR {p.step6_final_fare:.2f} "
            f"(+INR {p.step6_surcharge:.2f})"
        )

    print("=" * 68)
    print(f" Booking Subtotal ({len(passengers)} passenger{'s' if len(passengers) > 1 else ''}):  INR {subtotal:>10.2f}")

    if promo_result.code_applied:
        print(
            f" Promo Code Discount ({promo_result.code_applied}):    -INR {promo_result.discount_amount:>10.2f}"
        )
    else:
        print(f" Promo Code Discount:                   INR {Decimal('0.00'):>10.2f}")

    print("-" * 68)
    print(f" FINAL PAYABLE AMOUNT:                 INR {promo_result.final_total:>10.2f}")
    print("=" * 68)
    print(" Thank you for choosing ADG Railway! Have a safe journey.")
    print("=" * 68 + "\n")


def run_booking_flow() -> None:
    """Execute a single interactive booking cycle."""
    origin, destination, distance_km = select_route()
    train_type, travel_time_display = select_train(distance_km)
    travel_class = select_travel_class()
    passengers = intake_passengers(distance_km, train_type, travel_class)
    subtotal = fare.calculate_subtotal(passengers)
    promo_result = apply_promotions(subtotal)

    display_invoice(
        origin=origin,
        destination=destination,
        distance_km=distance_km,
        train_type=train_type,
        travel_time_display=travel_time_display,
        travel_class=travel_class,
        passengers=passengers,
        promo_result=promo_result,
    )


def main() -> None:
    """Application main loop."""
    display_banner()
    while True:
        try:
            run_booking_flow()
            print("Would you like to make another booking?")
            print("  [1] Yes, make another booking")
            print("  [2] Exit")
            choice = validation.prompt_menu_choice(
                prompt="Select an option (1-2): ",
                valid_options=["1", "2"],
            )
            if choice == "2":
                print("\nThank you for using ADG Railway Ticket Booking System. Goodbye!")
                break
        except (KeyboardInterrupt, EOFError):
            print("\n\nSession terminated by user. Goodbye!")
            sys.exit(0)
        except Exception as err:
            print(f"\nAn unexpected error occurred during booking: {err}")
            print("Restarting menu...")


if __name__ == "__main__":
    main()
