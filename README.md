# ADG Railway Ticket Booking System

A modular, interactive command-line Railway Ticket Booking System developed in Python for the ADG VIT Python Recruitment Task.

The system manages passenger intake, bidirectional route lookups, layered multi-step fare calculations, baggage weight checks, and promotional discounts to produce itemized booking invoices.

---

## 1. Project Directory Structure

```text
ADG/
├── routes.py               # Static route network, distances, train types, and class specifications
├── fare.py                 # Pure 6-step fare calculation engine & promotional code logic
├── validation.py           # Robust, crash-proof interactive input sanitization helpers
├── main.py                 # CLI driver, workflow coordinator, and terminal invoice renderer
├── README.md               # Documentation, architecture, setup, and test instructions
└── tests/
    ├── __init__.py         # Package marker
    ├── test_routes.py      # Unit tests for route symmetry, train specs, and travel times
    ├── test_fare.py        # Unit tests for the 6-step calculation pipeline & promo codes
    ├── test_validation.py  # Unit tests for input validation, edge cases, and bounds
    └── test_integration.py # End-to-end integration tests of complete booking sessions
```

---

## 2. Module Responsibilities & Modularity

The project adheres strictly to **separation of concerns**:

| Module | Core Responsibility | Restrictions |
| :--- | :--- | :--- |
| **`routes.py`** | Stores all static route pairs, distances, train types (speeds, surcharges, multipliers), and travel classes (multipliers, free baggage allowances). Contains lookup functions. | **No** fare calculation formulas, business logic, or interactive UI. |
| **`fare.py`** | Implements the pure 6-step fare calculation pipeline, subtotal aggregation, and promotional code engine using standard `Decimal` arithmetic. | **No** `input()` or `print()` calls; zero UI logic. |
| **`validation.py`** | Reusable, crash-proof input helpers (`prompt_int`, `prompt_float`, `prompt_menu_choice`, `prompt_passenger_name`, `prompt_age`, `prompt_baggage_weight`). Rejects invalid strings, non-finite floats (`NaN`, `Inf`), out-of-range choices, negative ages, and non-positive baggage. | **No** hardcoded business data or routing tables. |
| **`main.py`** | Coordinates the user journey through terminal menus, intake loops, module delegation, and invoice formatting. | **No** math calculations or static data tables. |
| **`tests/`** | Exhaustive unit and integration test suite using Python's built-in `unittest` framework. | 100% automated, standalone, zero external dependencies. |

---

## 3. Specifications & Business Rules

### Available Routes (Bidirectional)
The system models 10 bidirectional routes across 5 primary stations (`New Delhi`, `Mumbai`, `Kolkata`, `Chennai`, `Hyderabad`):
- New Delhi ↔ Mumbai: 1,460 km
- New Delhi ↔ Kolkata: 1,525 km
- New Delhi ↔ Chennai: 2,200 km
- New Delhi ↔ Hyderabad: 1,670 km
- Mumbai ↔ Kolkata: 1,970 km
- Mumbai ↔ Chennai: 1,300 km
- Mumbai ↔ Hyderabad: 711 km
- Kolkata ↔ Chennai: 1,200 km
- Kolkata ↔ Hyderabad: 1,600 km
- Chennai ↔ Hyderabad: 633 km

Distance lookups are strictly symmetric: `get_distance(A, B) == get_distance(B, A)`.

### Train Types
Travel time is calculated as $\text{Distance} \div \text{Average Speed}$:
- **Superfast:** 120 km/hr | Premium Multiplier: 1.50× | Flat Surcharge: +INR 100
- **Express:** 110 km/hr | Premium Multiplier: 1.25× | Flat Surcharge: +INR 50
- **Fast Passenger:** 90 km/hr | Premium Multiplier: 1.00× | Flat Surcharge: +INR 0

### Travel Classes
- **Sleeper:** Multiplier: 1.0× | Free Baggage Allowance: 20 kg
- **AC 3-Tier:** Multiplier: 1.5× | Free Baggage Allowance: 30 kg
- **AC 2-Tier:** Multiplier: 2.0× | Free Baggage Allowance: 40 kg

---

## 4. The 6-Step Fare Calculation Pipeline

Each passenger's fare is evaluated **independently** in this exact order:

1. **Step 1 — Slab Fare:**
   - Flat base fare of **INR 100.00**.
   - Distance slab rates:
     - First 100 km: **INR 1.00** per km
     - Next 200 km (101 to 300 km): **INR 0.80** per km
     - Beyond 300 km: **INR 0.60** per km
2. **Step 2 — Senior Citizen Discount:**
   - If passenger age is **strictly above 60** (`age > 60`), apply a **40% discount** to the Step 1 total. (Age 60 receives no discount).
3. **Step 3 — Train Premium:**
   - Multiply the Step 2 result by the selected train premium (1.00×, 1.25×, or 1.50×).
4. **Step 4 — Class Premium:**
   - Multiply the Step 3 result by the travel class multiplier (1.0×, 1.5×, or 2.0×).
5. **Step 5 — Excess Baggage Fee:**
   - If declared baggage weight exceeds class free allowance, a penalty of **INR 15.00** per excess kilogram is added.
   - **Documented Interpretation (Option A):** Fractional excess baggage is charged proportionally (e.g., 5.5 kg excess incurs $5.5 \times 15 = \text{INR } 82.50$) with monetary rounding to two decimal places.
6. **Step 6 — Flat Surcharge:**
   - Add the final flat surcharge based on train type (+INR 100 for Superfast, +INR 50 for Express, +INR 0 for Fast Passenger).

### Subtotal & Promo Code Engine
- Individual passenger final fares are summed to produce the **Booking Subtotal**.
- **Supported Promo Codes (Case-Insensitive):**
  - **`ADG20`**: Deducts flat 20% off the subtotal.
  - **`WINTER500`**: Deducts flat INR 500 off the subtotal, clamped to never drop the payable amount below **INR 0.00**.
  - Blank input: Proceeds without discount.
  - Invalid code: Informs the user and proceeds without discount.
  - Maximum of one promo code allowed per booking.

---

## 5. System Requirements & Setup

- **Python Version:** Python 3.8 or higher (tested on Python 3.13).
- **External Dependencies:** **None**. Uses standard library modules (`decimal`, `dataclasses`, `math`, `sys`, `typing`, `unittest`).

---

## 6. How to Run the Application

From the project root directory:

```bash
python main.py
```

### Keyboard Shortcuts & Graceful Termination
- To exit the program, select the exit option in the menu or press `Ctrl + C` (`KeyboardInterrupt`) / `Ctrl + Z` (`EOF`).

---

## 7. How to Run Automated Tests

The test suite runs through Python's standard `unittest` discovery runner with zero extra setup:

```bash
python -m unittest discover -v
```

To run individual test suites:
```bash
python -m unittest tests.test_routes -v
python -m unittest tests.test_fare -v
python -m unittest tests.test_validation -v
python -m unittest tests.test_integration -v
```

---

## 8. Sample Booking Session & Expected Output

### Input Scenario:
- **Route:** New Delhi to Mumbai (1,460 km)
- **Train:** Superfast (120 km/h, +INR 100 surcharge)
- **Class:** AC 3-Tier (1.5× multiplier, 30 kg free baggage)
- **Passengers (2):**
  1. *Ashok Kumar*, Age: 65 (Senior Citizen), Baggage: 35.0 kg (5.0 kg excess)
  2. *Sneha Kumar*, Age: 28, Baggage: 25.0 kg (0.0 kg excess)
- **Promo Code:** `ADG20`

### Invoice Output:
```text
====================================================================
                     OFFICIAL BOOKING INVOICE
====================================================================
 Route:               New Delhi <-> Mumbai
 Distance:            1,460 km
 Train Type:          Superfast
 Estimated Time:      12 hrs 10 mins (12.17 hrs)
 Travel Class:        AC 3-Tier
--------------------------------------------------------------------
 PASSENGER BREAKDOWN:
 #   Name               Age   Baggage    Senior Disc   Excess Fee     Fare
--------------------------------------------------------------------
 1   Ashok Kumar        65    35.0 kg    -INR 422.40   +INR 75.00   INR 1600.60
 2   Sneha Kumar        28    25.0 kg    None          INR 0.00     INR 2476.00
--------------------------------------------------------------------
 STEP-BY-STEP AUDIT TRAIL (Per Passenger):
 Passenger 1 (Ashok Kumar):
   Step 1 (Base Slab Fare):         INR 1056.00
   Step 2 (After Senior Citizen):   INR 633.60 (-40%)
   Step 3 (Train Premium 1.50x):     INR 950.40
   Step 4 (Class Multiplier 1.5x):  INR 1425.60
   Step 5 (Excess Baggage Fee):     INR 1500.60 (+5.00 kg excess)
   Step 6 (Train Flat Surcharge):   INR 1600.60 (+INR 100.00)
 Passenger 2 (Sneha Kumar):
   Step 1 (Base Slab Fare):         INR 1056.00
   Step 2 (After Senior Citizen):   INR 1056.00 (No discount)
   Step 3 (Train Premium 1.50x):     INR 1584.00
   Step 4 (Class Multiplier 1.5x):  INR 2376.00
   Step 5 (Excess Baggage Fee):     INR 2376.00 (+0.00 kg excess)
   Step 6 (Train Flat Surcharge):   INR 2476.00 (+INR 100.00)
====================================================================
 Booking Subtotal (2 passengers):  INR    4076.60
 Promo Code Discount (ADG20):    -INR     815.32
--------------------------------------------------------------------
 FINAL PAYABLE AMOUNT:                 INR    3261.28
====================================================================
```

---

## 9. Assumptions & Documented Decisions

1. **Fractional Baggage Charges:** Calculated proportionally at INR 15.00 per excess kg and quantized to 2 decimal places using `ROUND_HALF_UP`.
2. **Senior Citizen Threshold:** Strictly above 60 (`age > 60`). Age 60 pays full fare; age 61+ receives the 40% discount.
3. **Age Validation Bounds:** Passenger ages are validated between 1 and 120 (inclusive).
4. **Baggage Weight Bounds:** Declared baggage weight must be strictly positive ($> 0\text{ kg}$) and $\le 200\text{ kg}$.
5. **Zero Floor for Promotions:** Discount amount on `WINTER500` is capped at the subtotal so that the payable amount cannot become negative.
