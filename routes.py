"""routes.py - Route network, train specifications, and travel class data.

This module stores all static route and distance data, train type specifications,
and travel class allowances as specified in the ADG Railway Ticket Booking System.
No fare calculations, business logic, or user-interface code reside here.
"""

from typing import Dict, List, Optional, Tuple

# Available Stations in the Network
STATIONS: List[str] = [
    "New Delhi",
    "Mumbai",
    "Kolkata",
    "Chennai",
    "Hyderabad",
]

# Exact 10 Bidirectional Routes and Distances (in kilometers)
# Represented canonically as frozensets or sorted tuples of station pairs.
_ROUTE_DISTANCES_KM: Dict[Tuple[str, str], int] = {
    ("Mumbai", "New Delhi"): 1460,
    ("Kolkata", "New Delhi"): 1525,
    ("Chennai", "New Delhi"): 2200,
    ("Hyderabad", "New Delhi"): 1670,
    ("Kolkata", "Mumbai"): 1970,
    ("Chennai", "Mumbai"): 1300,
    ("Hyderabad", "Mumbai"): 711,
    ("Chennai", "Kolkata"): 1200,
    ("Hyderabad", "Kolkata"): 1600,
    ("Chennai", "Hyderabad"): 633,
}

# Train Specifications
# Superfast: 120 km/hr, 1.50x premium, INR 100 surcharge
# Express: 110 km/hr, 1.25x premium, INR 50 surcharge
# Fast Passenger: 90 km/hr, 1.00x premium, INR 0 surcharge
TRAIN_TYPES: Dict[str, Dict[str, object]] = {
    "Superfast": {
        "name": "Superfast",
        "speed_kmh": 120,
        "premium_multiplier": 1.50,
        "flat_surcharge": 100.0,
    },
    "Express": {
        "name": "Express",
        "speed_kmh": 110,
        "premium_multiplier": 1.25,
        "flat_surcharge": 50.0,
    },
    "Fast Passenger": {
        "name": "Fast Passenger",
        "speed_kmh": 90,
        "premium_multiplier": 1.00,
        "flat_surcharge": 0.0,
    },
}

# Travel Classes Specifications
# Sleeper: 1.0x multiplier, 20 kg free allowance
# AC 3-Tier: 1.5x multiplier, 30 kg free allowance
# AC 2-Tier: 2.0x multiplier, 40 kg free allowance
TRAVEL_CLASSES: Dict[str, Dict[str, object]] = {
    "Sleeper": {
        "name": "Sleeper",
        "multiplier": 1.0,
        "free_baggage_kg": 20.0,
    },
    "AC 3-Tier": {
        "name": "AC 3-Tier",
        "multiplier": 1.5,
        "free_baggage_kg": 30.0,
    },
    "AC 2-Tier": {
        "name": "AC 2-Tier",
        "multiplier": 2.0,
        "free_baggage_kg": 40.0,
    },
}


def _canonical_key(station_a: str, station_b: str) -> Tuple[str, str]:
    """Return a canonical sorted tuple for bidirectional lookup."""
    a = station_a.strip()
    b = station_b.strip()
    return (a, b) if a < b else (b, a)


def get_stations() -> List[str]:
    """Return a copy of the available stations list."""
    return list(STATIONS)


def get_destinations(origin: str) -> List[str]:
    """Return all valid destinations reachable from the given origin."""
    origin_clean = origin.strip()
    if origin_clean not in STATIONS:
        raise ValueError(f"Unknown station: '{origin}'")
    return [s for s in STATIONS if s != origin_clean]


def get_distance(origin: str, destination: str) -> int:
    """Retrieve the distance in km between two stations.

    Bidirectional: get_distance(A, B) == get_distance(B, A).
    Raises ValueError if stations are identical or either station is invalid.
    """
    origin_clean = origin.strip()
    dest_clean = destination.strip()

    if origin_clean not in STATIONS:
        raise ValueError(f"Origin station '{origin}' is not recognized.")
    if dest_clean not in STATIONS:
        raise ValueError(f"Destination station '{destination}' is not recognized.")
    if origin_clean == dest_clean:
        raise ValueError("Origin and destination cannot be the same station.")

    key = _canonical_key(origin_clean, dest_clean)
    if key in _ROUTE_DISTANCES_KM:
        return _ROUTE_DISTANCES_KM[key]

    raise ValueError(f"No direct route found between '{origin_clean}' and '{dest_clean}'.")


def get_train_specs(train_type: str) -> Dict[str, object]:
    """Retrieve the specifications for a given train type."""
    train_clean = train_type.strip()
    for name, specs in TRAIN_TYPES.items():
        if name.lower() == train_clean.lower():
            return dict(specs)
    valid_names = ", ".join(TRAIN_TYPES.keys())
    raise ValueError(f"Invalid train type '{train_type}'. Valid types: {valid_names}")


def get_class_specs(travel_class: str) -> Dict[str, object]:
    """Retrieve the specifications for a given travel class."""
    class_clean = travel_class.strip()
    for name, specs in TRAVEL_CLASSES.items():
        if name.lower() == class_clean.lower():
            return dict(specs)
    valid_classes = ", ".join(TRAVEL_CLASSES.keys())
    raise ValueError(f"Invalid travel class '{travel_class}'. Valid classes: {valid_classes}")


def calculate_travel_time(distance_km: float, train_type: str) -> Tuple[float, int, int]:
    """Calculate the estimated travel time given distance and train type.

    Returns:
        tuple: (total_hours_float, hours_int, minutes_int)
    """
    specs = get_train_specs(train_type)
    speed = float(specs["speed_kmh"])
    if speed <= 0:
        raise ValueError("Train speed must be positive.")

    total_hours = distance_km / speed
    hours = int(total_hours)
    minutes = int(round((total_hours - hours) * 60))
    if minutes == 60:
        hours += 1
        minutes = 0

    return (total_hours, hours, minutes)
