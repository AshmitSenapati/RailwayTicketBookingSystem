"""validation.py - Crash-proof interactive input validation helpers.

This module provides reusable, robust input collection functions for the command-line
interface. It ensures that invalid string formats, out-of-range menu selections,
non-finite numbers (NaN, Inf), negative/zero baggage weights, and invalid ages
are gracefully caught and re-prompted without ever crashing the application.

Design Rules:
- No hardcoded routes, train types, travel classes, or fare calculations.
- Functions handle repetitive prompting until valid input is received.
- Easily testable via `unittest.mock.patch('builtins.input', ...)`.
"""

import math
from typing import Iterable, List, Optional, Sequence, Union


def prompt_int(
    prompt: str,
    min_val: Optional[int] = None,
    max_val: Optional[int] = None,
) -> int:
    """Prompt for a valid integer within the optional inclusive range [min_val, max_val].

    Re-prompts cleanly upon receiving non-numeric text, blank lines, or out-of-range integers.
    """
    while True:
        try:
            raw = input(prompt).strip()
            if not raw:
                print("Error: Input cannot be blank. Please enter a whole number.")
                continue

            val = int(raw)

            if min_val is not None and max_val is not None and not (min_val <= val <= max_val):
                print(f"Error: Value must be between {min_val} and {max_val} (inclusive).")
                continue
            if min_val is not None and val < min_val:
                print(f"Error: Value cannot be less than {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print(f"Error: Value cannot be greater than {max_val}.")
                continue

            return val
        except ValueError:
            print("Error: Invalid input. Please enter a valid whole number (integer).")


def prompt_float(
    prompt: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    exclusive_min: Optional[float] = None,
) -> float:
    """Prompt for a finite floating-point or integer number with optional bounds.

    Rejects non-finite values (NaN, Inf, -Inf), blank entries, non-numeric strings,
    and out-of-range inputs.

    Args:
        prompt: Display text for user input.
        min_val: Optional inclusive lower bound.
        max_val: Optional inclusive upper bound.
        exclusive_min: Optional strict lower bound (value must be strictly > exclusive_min).
    """
    while True:
        try:
            raw = input(prompt).strip()
            if not raw:
                print("Error: Input cannot be blank. Please enter a number.")
                continue

            val = float(raw)

            if not math.isfinite(val):
                print("Error: Non-finite numbers (NaN, Infinity) are not permitted.")
                continue

            if exclusive_min is not None and val <= exclusive_min:
                print(f"Error: Value must be strictly greater than {exclusive_min}.")
                continue
            if min_val is not None and max_val is not None and not (min_val <= val <= max_val):
                print(f"Error: Value must be between {min_val} and {max_val} (inclusive).")
                continue
            if min_val is not None and val < min_val:
                print(f"Error: Value cannot be less than {min_val}.")
                continue
            if max_val is not None and val > max_val:
                print(f"Error: Value cannot be greater than {max_val}.")
                continue

            return val
        except ValueError:
            print("Error: Invalid numeric input. Please enter a valid number.")


def prompt_menu_choice(
    prompt: str,
    valid_options: Sequence[Union[str, int]],
    case_sensitive: bool = False,
) -> str:
    """Prompt for an explicit menu choice from a permitted sequence of options.

    Args:
        prompt: Prompt message to display.
        valid_options: Iterable of acceptable choices (e.g. ['1', '2', '3']).
        case_sensitive: Whether string comparison should be case-sensitive.
    """
    options_list = [str(opt).strip() for opt in valid_options]
    if not options_list:
        raise ValueError("valid_options list cannot be empty.")

    if case_sensitive:
        allowed_lookup = {opt: opt for opt in options_list}
    else:
        allowed_lookup = {opt.lower(): opt for opt in options_list}

    while True:
        raw = input(prompt).strip()
        if not raw:
            print(f"Error: Selection cannot be empty. Permitted options: {', '.join(options_list)}")
            continue

        key = raw if case_sensitive else raw.lower()
        if key in allowed_lookup:
            return allowed_lookup[key]

        print(
            f"Error: Invalid choice '{raw}'. Please enter one of: {', '.join(options_list)}"
        )


def prompt_passenger_name(prompt: str = "Enter passenger name: ") -> str:
    """Prompt for passenger name, rejecting empty or whitespace-only inputs."""
    while True:
        raw = input(prompt).strip()
        if not raw:
            print("Error: Passenger name cannot be blank. Please enter a valid name.")
            continue
        return raw


def prompt_age(prompt: str = "Enter passenger age (1-120): ") -> int:
    """Prompt for a valid passenger age between 1 and 120 (inclusive) using prompt_int."""
    return prompt_int(prompt, min_val=1, max_val=120)


def prompt_baggage_weight(
    prompt: str = "Enter baggage weight in kg: ",
    max_val: float = 200.0,
) -> float:
    """Prompt for a strictly positive baggage weight (> 0 kg) using prompt_float."""
    return prompt_float(prompt, max_val=max_val, exclusive_min=0.0)


def prompt_optional_text(prompt: str) -> Optional[str]:
    """Prompt for optional text (e.g. promo code).

    Returns None if the user enters nothing or only whitespace, else the stripped string.
    """
    raw = input(prompt).strip()
    return raw if raw else None
