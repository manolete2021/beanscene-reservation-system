"""Tests for the floor plan (2-D grid)."""

import pytest

from beanscene import floor_plan


@pytest.fixture
def floor():
    """A fresh floor for each test: rows A, B and C, 10 tables each, as in config.json."""
    return floor_plan.create_floor(["A", "B", "C"], 10)


def test_floor_has_thirty_tables_indexed_by_row_and_column(floor):
    assert len(floor) == 3
    assert len(floor[0]) == 10
    assert floor_plan.occupancy(floor) == (0, 30)
    assert floor[0][3]["code"] == "A4"
    assert floor[0][9]["code"] == "A10"
    assert floor[1][0]["code"] == "B1"
    assert floor[2][9]["code"] == "C10"
    assert floor_plan.parse_table_code(floor, "a4") == (0, 3)


def test_all_tables_start_free(floor):
    assert floor_plan.occupancy(floor) == (0, 30)
    codes = floor_plan.free_table_codes(floor)
    assert codes == [
        "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10",
        "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10",
        "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10",
    ]
    for row in floor:
        for table in row:
            assert table["booking_reference"] is None


def test_more_rows_from_settings_still_work():
    two_rows = floor_plan.create_floor(["A", "B"], 5)
    assert floor_plan.occupancy(two_rows) == (0, 10)
    assert floor_plan.get_table(two_rows, "B3") is two_rows[1][2]


def test_seat_at_free_table_then_free_it_again(floor):
    floor_plan.assign_booking(floor, "A4", "BS-10432")
    assert floor_plan.read_occupant(floor, "A4") == "BS-10432"
    assert floor_plan.occupancy(floor) == (1, 30)
    assert "A4" not in floor_plan.free_table_codes(floor)
    assert len(floor_plan.free_table_codes(floor)) == 29
    floor_plan.release_table(floor, "A4")
    assert floor_plan.read_occupant(floor, "A4") is None
    assert floor_plan.occupancy(floor) == (0, 30)
    assert "A4" in floor_plan.free_table_codes(floor)
    assert len(floor_plan.free_table_codes(floor)) == 30


def test_occupied_table_is_refused(floor):
    floor_plan.assign_booking(floor, "A4", "BS-10432")
    with pytest.raises(ValueError, match="already occupied"):
        floor_plan.assign_booking(floor, "A4", "BS-10433")


def test_freeing_a_free_table_is_refused(floor):
    with pytest.raises(ValueError, match="already free"):
        floor_plan.release_table(floor, "A1")


@pytest.mark.parametrize("bad_code", ["A0", "A11", "D1", "A", "44", ""])
def test_unknown_table_codes_are_refused(floor, bad_code):
    with pytest.raises(ValueError, match="not a table"):
        floor_plan.get_table(floor, bad_code)


def test_lowercase_and_surrounding_spaces_are_accepted(floor):
    assert floor_plan.parse_table_code(floor, " a4 ") == (0, 3)
    assert floor_plan.get_table(floor, "  c10")["code"] == "C10"
    floor_plan.assign_booking(floor, " b2 ", "BS-10432")
    assert floor_plan.read_occupant(floor, "b2") == "BS-10432"
