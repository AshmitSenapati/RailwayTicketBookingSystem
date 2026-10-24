"""Unit tests for routes.py."""

import unittest
from routes import (
    STATIONS,
    TRAIN_TYPES,
    TRAVEL_CLASSES,
    calculate_travel_time,
    get_class_specs,
    get_destinations,
    get_distance,
    get_stations,
    get_train_specs,
)


class TestRoutes(unittest.TestCase):
    """Test suite verifying route lookups, train specs, and class specs."""

    def test_station_count_and_uniqueness(self):
        """Verify the 5 expected stations are unique and present."""
        stations = get_stations()
        self.assertEqual(len(stations), 5)
        self.assertEqual(len(set(stations)), 5)
        expected = {"New Delhi", "Mumbai", "Kolkata", "Chennai", "Hyderabad"}
        self.assertEqual(set(stations), expected)

    def test_all_10_bidirectional_routes(self):
        """Verify all 10 specified routes return exact distances in both directions."""
        expected_routes = [
            ("New Delhi", "Mumbai", 1460),
            ("New Delhi", "Kolkata", 1525),
            ("New Delhi", "Chennai", 2200),
            ("New Delhi", "Hyderabad", 1670),
            ("Mumbai", "Kolkata", 1970),
            ("Mumbai", "Chennai", 1300),
            ("Mumbai", "Hyderabad", 711),
            ("Kolkata", "Chennai", 1200),
            ("Kolkata", "Hyderabad", 1600),
            ("Chennai", "Hyderabad", 633),
        ]

        self.assertEqual(len(expected_routes), 10)

        for origin, dest, distance in expected_routes:
            # Forward lookup
            self.assertEqual(
                get_distance(origin, dest),
                distance,
                f"Failed for forward route {origin} -> {dest}",
            )
            # Reverse lookup
            self.assertEqual(
                get_distance(dest, origin),
                distance,
                f"Failed for reverse route {dest} -> {origin}",
            )

    def test_same_origin_and_destination_raises_error(self):
        """Verify selecting identical origin and destination raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            get_distance("Mumbai", "Mumbai")
        self.assertIn("cannot be the same station", str(ctx.exception).lower())

    def test_invalid_station_raises_error(self):
        """Verify invalid station names raise ValueError."""
        with self.assertRaises(ValueError):
            get_distance("Bangalore", "Mumbai")
        with self.assertRaises(ValueError):
            get_distance("Mumbai", "Goa")

    def test_get_destinations(self):
        """Verify destination list excludes the origin station."""
        destinations = get_destinations("New Delhi")
        self.assertEqual(len(destinations), 4)
        self.assertNotIn("New Delhi", destinations)
        self.assertIn("Mumbai", destinations)

    def test_train_specifications(self):
        """Verify train types have the exact speeds, multipliers, and surcharges."""
        superfast = get_train_specs("Superfast")
        self.assertEqual(superfast["speed_kmh"], 120)
        self.assertEqual(superfast["premium_multiplier"], 1.50)
        self.assertEqual(superfast["flat_surcharge"], 100.0)

        express = get_train_specs("Express")
        self.assertEqual(express["speed_kmh"], 110)
        self.assertEqual(express["premium_multiplier"], 1.25)
        self.assertEqual(express["flat_surcharge"], 50.0)

        passenger = get_train_specs("Fast Passenger")
        self.assertEqual(passenger["speed_kmh"], 90)
        self.assertEqual(passenger["premium_multiplier"], 1.00)
        self.assertEqual(passenger["flat_surcharge"], 0.0)

    def test_case_insensitive_train_lookup(self):
        """Verify train lookup is case-insensitive."""
        specs = get_train_specs("superfast")
        self.assertEqual(specs["name"], "Superfast")

    def test_invalid_train_type_raises_error(self):
        """Verify an invalid train type raises ValueError."""
        with self.assertRaises(ValueError):
            get_train_specs("Bullet Train")

    def test_travel_class_specifications(self):
        """Verify travel classes have exact multipliers and baggage allowances."""
        sleeper = get_class_specs("Sleeper")
        self.assertEqual(sleeper["multiplier"], 1.0)
        self.assertEqual(sleeper["free_baggage_kg"], 20.0)

        ac3 = get_class_specs("AC 3-Tier")
        self.assertEqual(ac3["multiplier"], 1.5)
        self.assertEqual(ac3["free_baggage_kg"], 30.0)

        ac2 = get_class_specs("AC 2-Tier")
        self.assertEqual(ac2["multiplier"], 2.0)
        self.assertEqual(ac2["free_baggage_kg"], 40.0)

    def test_invalid_travel_class_raises_error(self):
        """Verify an invalid travel class raises ValueError."""
        with self.assertRaises(ValueError):
            get_class_specs("First Class")

    def test_travel_time_calculation(self):
        """Verify travel time calculation (hours and minutes)."""
        # 1460 km on Superfast (120 km/h) = 12.166667 hours -> 12 hrs 10 mins
        total_hours, hours, minutes = calculate_travel_time(1460, "Superfast")
        self.assertAlmostEqual(total_hours, 12.1666667, places=4)
        self.assertEqual(hours, 12)
        self.assertEqual(minutes, 10)

        # 633 km on Fast Passenger (90 km/h) = 7.033333 hours -> 7 hrs 2 mins
        total_hours, hours, minutes = calculate_travel_time(633, "Fast Passenger")
        self.assertAlmostEqual(total_hours, 7.033333, places=4)
        self.assertEqual(hours, 7)
        self.assertEqual(minutes, 2)


if __name__ == "__main__":
    unittest.main()
