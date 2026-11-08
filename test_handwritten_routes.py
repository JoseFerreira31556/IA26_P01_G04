"""
Point 13 - Tests with hand-written routes (real data from the tiny dataset).

Routes tested with checkRoute from model.py (point 12):
  1) a valid route
  2) a route that exceeds the vehicle capacity
  3) a route outside the time windows (late pickup and late delivery)
  + an extra flow test (delivering an item that was never loaded at the warehouse)

How to run:
  - terminal:  python test_handwritten_routes.py
  - notebook:  import test_handwritten_routes; test_handwritten_routes.run_all()

Ids used (location_id): producers 1, 2, 3 | collection center 4 (warehouse) | deliveries 5 to 9.
Vehicles: 1 (150 kg, refrigerated) and 2 (200 kg), both based at center 4.

Note: the tests look for the error messages produced by checkRoute in model.py
("outside the time window", "kg on board", ...). If those messages change, update the asserts.
"""
import os

from model import read_csv_files, loadProblem, buildCheckData, checkRoute

DATASET_PATH = os.environ.get("TINY_DATASET_PATH", "./data/data_tiny_20261020/")


def load_data(path=DATASET_PATH):
    # Loads the CSV files and builds the dictionary that checkRoute expects
    files_list = sorted(os.listdir(path))
    problem = loadProblem(read_csv_files(path, files_list))
    return buildCheckData(problem)


DATA = load_data()


# --------------------------------------------------------------------------
# TESTS  (route = list of stops (location_id, [order_item_id, ...]))
# --------------------------------------------------------------------------
def test_valid_route():
    """
    Order 4 (items 11, 12, 13 = 26.3 kg) with vehicle 2 (200 kg), starting at 08:00 on 30 Oct.
    Picks up at producers 3, 2 and 1, goes through the warehouse (4) and delivers at Casa 3 (location 7).
    Expected: feasible, no errors.
    """
    route = [
        (3, [11]),
        (2, [12]),
        (1, [13]),
        (4, [11, 12, 13]),
        (7, [11, 12, 13]),
    ]
    errors = checkRoute(DATA, 2, route, "2026-10-30 08:00")
    assert errors == [], f"the route should be valid, but: {errors}"


def test_exceeds_capacity():
    """
    Vehicle 1 (150 kg) picks up ALL 24 items with pickup on 30 Oct (166.9 kg):
    producer 3 (37.3 kg) -> producer 1 (52.0 kg) -> producer 2 (77.6 kg) -> warehouse.
    Expected: infeasible only because of capacity (166.9 kg > 150 kg at stop 3).
    """
    route = [
        (3, [6, 11, 22, 24, 26, 29, 35]),
        (1, [5, 13, 25, 31, 32, 34, 37, 40]),
        (2, [12, 23, 27, 28, 30, 33, 36, 38, 39]),
        (4, []),
    ]
    errors = checkRoute(DATA, 1, route, "2026-10-30 07:00")
    assert len(errors) == 1, f"there should be exactly 1 error, but: {errors}"
    assert "166.9 kg on board" in errors[0] and "150 kg" in errors[0], errors


def test_outside_window_pickup():
    """
    Order 2 (items 5 and 6) with vehicle 2, leaving at 09:30 on 30 Oct.
    Item 6 (producer 3) can only be picked up until 09:45, but the vehicle arrives at 10:08.
    Item 5 (producer 1, until 11:15) is still on time.
    Expected: infeasible only because item 6 is outside its window, at stop 1.
    """
    route = [
        (3, [6]),
        (1, [5]),
        (4, [5, 6]),
        (8, [5, 6]),
    ]
    errors = checkRoute(DATA, 2, route, "2026-10-30 09:30")
    assert len(errors) == 1, f"there should be exactly 1 error, but: {errors}"
    assert "Stop 1" in errors[0] and "item 6" in errors[0] and "outside the time window" in errors[0], errors


def test_outside_window_delivery():
    """
    Item 12 (10.3 kg; producer 2 -> Casa 3, location 7) with vehicle 2, leaving at 11:00 on 30 Oct.
    The pickup is still on time (11:50, window until 12:00), but the delivery only arrives at about
    13:51 and the delivery window closes at 13:45.
    Expected: infeasible only because item 12 is outside its window at the delivery (stop 3).
    """
    route = [
        (2, [12]),
        (4, [12]),
        (7, [12]),
    ]
    errors = checkRoute(DATA, 2, route, "2026-10-30 11:00")
    assert len(errors) == 1, f"there should be exactly 1 error, but: {errors}"
    assert "Stop 3" in errors[0] and "item 12" in errors[0] and "outside the time window" in errors[0], errors


def test_extra_flow_without_warehouse():
    """
    Extra: try to deliver item 11 without having picked it up or loaded it at the warehouse.
    Expected: infeasible, the item was not loaded at the warehouse.
    """
    route = [(7, [11])]
    errors = checkRoute(DATA, 2, route, "2026-10-30 08:00")
    assert any("was not loaded at the warehouse" in e for e in errors), errors


# --------------------------------------------------------------------------
def run_all():
    """Runs all the tests and prints a summary (useful in the notebook, no pytest needed)."""
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"OK    {test.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL  {test.__name__}: {e}")
    print(f"\n{len(tests) - failures}/{len(tests)} tests passed")
    return failures == 0


if __name__ == "__main__":
    raise SystemExit(0 if run_all() else 1)