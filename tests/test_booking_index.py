"""Tests for the hash-table booking index and the booking rules."""

import pytest

from beanscene import booking_index, bookings, floor_plan
from beanscene.records import make_booking

RULES = {"reference_prefix": "BS-", "first_reference_number": 10400, "max_party_size": 12,
         "sources": ["in person", "email", "phone"]}

def test_hash_adds_character_codes_mod_16():
    assert booking_index.hash_reference("BS-10432", 16) == 444 % 16 == 12
    assert booking_index.explain_hash("BS-10432", 16).endswith("= 444; 444 mod 16 = 12")

def test_collision_both_bookings_still_found():
    index = booking_index.new_index(16)
    first = booking_index.index_add(index, make_booking("BS-10432", "Siobhan O'Brien", 2, "email"))
    second = booking_index.index_add(index, make_booking("BS-10423", "Hannah Lee", 3, "phone"))
    assert first == second == 12                        # same bucket: a collision
    assert booking_index.bucket_sizes(index)[12] == 2   # chained in one bucket
    assert booking_index.index_find(index, "BS-10432")["guest_name"] == "Siobhan O'Brien"
    assert booking_index.index_find(index, "bs-10423")["guest_name"] == "Hannah Lee"
    assert booking_index.index_find(index, "BS-99999") is None

def test_duplicate_reference_is_refused():
    index = booking_index.new_index(16)
    booking_index.index_add(index, make_booking("BS-10432", "A", 2, "email"))
    with pytest.raises(ValueError, match="already exists"):
        booking_index.index_add(index, make_booking("BS-10432", "B", 2, "email"))

def test_seat_then_complete_frees_the_table():
    floor = floor_plan.create_floor(["A"], 30)
    booking = make_booking("BS-10432", "Siobhan O'Brien", 2, "email")
    bookings.seat_booking(booking, floor, "A4")
    assert booking["status"] == "seated" and booking["table_code"] == "A4"
    bookings.complete_booking(booking, floor)
    assert booking["status"] == "completed" and floor_plan.read_occupant(floor, "A4") is None

def test_cancel_seated_booking_frees_the_table():
    floor = floor_plan.create_floor(["A"], 30)
    booking = make_booking("BS-10432", "Siobhan O'Brien", 2, "email")
    bookings.seat_booking(booking, floor, "A29")
    bookings.cancel_booking(booking, floor)
    assert floor_plan.read_occupant(floor, "A29") is None and booking["table_code"] is None

@pytest.mark.parametrize("start, change", [("completed", "seated"), ("cancelled", "seated"),
                                           ("pending", "completed"), ("completed", "cancelled")])
def test_changes_that_make_no_sense_are_refused(start, change):
    booking = make_booking("BS-10432", "Siobhan O'Brien", 2, "email")
    booking["status"] = start
    with pytest.raises(ValueError, match="cannot be changed"):
        bookings.check_change(booking, change)

def test_new_booking_details_are_checked():
    with pytest.raises(ValueError, match="Party size"):
        bookings.create_booking("BS-1", "Ann", 0, "phone", RULES)
    with pytest.raises(ValueError, match="must be one of"):
        bookings.create_booking("BS-1", "Ann", 2, "fax", RULES)

def test_next_reference_is_one_more_than_highest():
    existing = [make_booking("BS-10432", "A", 2, "email"), make_booking("BS-10441", "B", 2, "email")]
    assert bookings.next_reference(existing, RULES) == "BS-10442"
