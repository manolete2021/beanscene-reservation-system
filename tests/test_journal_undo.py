"""Tests for the 60-byte journal file, the undo stack and undo of each change."""

import pytest

import main
from beanscene import journal, operations, undo_stack, waitlist
from beanscene.records import make_undo_item, make_waiting_guest

@pytest.fixture
def state(tmp_path):
    """The program's full state, with the journal in a temporary folder."""
    settings = main.load_config()
    settings["files"]["journal"] = str(tmp_path / "journal.dat")
    built = main.build_state(settings)
    yield built
    journal.close_journal(built["journal"])

def test_record_is_exactly_60_bytes_and_reads_back(tmp_path):
    log = journal.open_journal(tmp_path / "j.dat")
    entry = journal.append_entry(log, "ST004", "SEAT BOOKING", "BS-10432")
    assert (tmp_path / "j.dat").stat().st_size == 60
    assert journal.read_entry(log, 0) == entry
    journal.close_journal(log)

def test_undo_flag_changes_one_byte_and_neighbours_are_unchanged(tmp_path):
    path = tmp_path / "j.dat"
    log = journal.open_journal(path)
    for number in range(3):
        journal.append_entry(log, "ST001", "NEW BOOKING", f"BS-1040{number}")
    before = path.read_bytes()
    journal.set_cancelled(log, 1)
    after = path.read_bytes()
    changed = [offset for offset in range(len(before)) if before[offset] != after[offset]]
    assert changed == [1 * 60 + 59]                     # exactly one byte, at offset 119
    assert journal.read_entry(log, 1)["cancelled"] is True
    assert after[:60] == before[:60] and after[120:] == before[120:]
    journal.close_journal(log)

def test_stack_is_last_in_first_out():
    stack = undo_stack.new_stack()
    undo_stack.push(stack, make_undo_item("FIRST", ""))
    undo_stack.push(stack, make_undo_item("SECOND", ""))
    assert undo_stack.pop(stack)["action"] == "SECOND"
    assert undo_stack.pop(stack)["action"] == "FIRST"
    with pytest.raises(ValueError, match="nothing to undo"):
        undo_stack.pop(stack)

def test_undo_reverses_the_most_recent_change(state):
    operations.seat(state, "BS-10432", "A4")
    operations.complete(state, "BS-10432")
    operations.undo_last(state)                         # undo the complete
    booking = operations.find_booking(state, "BS-10432")
    assert booking["status"] == "seated" and booking["table_code"] == "A4"
    assert journal.read_entry(state["journal"], 1)["cancelled"] is True
    assert journal.read_entry(state["journal"], 0)["cancelled"] is False
    operations.undo_last(state)                         # undo the seat
    assert booking["status"] == "pending" and state["floor"][0][3]["booking_reference"] is None

def test_undo_waitlist_changes(state):
    operations.waitlist_add(state, make_waiting_guest("Ana", 2), 0)
    operations.waitlist_add(state, make_waiting_guest("Ben", 2), 0)
    operations.waitlist_remove(state, 1)                # removes Ana
    operations.undo_last(state)                         # Ana comes back at position 2
    assert [guest["name"] for guest in waitlist.read_forwards(state["waitlist"])] == ["Ben", "Ana"]

def test_undo_that_is_no_longer_possible_changes_nothing(state):
    operations.seat(state, "BS-10432", "A4")
    operations.complete(state, "BS-10432")              # A4 free again
    operations.seat(state, "BS-10421", "A4")            # A4 given to someone else
    undo_stack.pop(state["undo"])                       # set the seat aside so COMPLETE is on top
    with pytest.raises(ValueError, match="given to another booking"):
        operations.undo_last(state)
    assert undo_stack.peek(state["undo"])["action"] == "COMPLETE BOOKING"

def test_every_change_is_journalled_with_the_staff_code(state):
    state["staff_code"] = "ST004"
    operations.new_booking(state, "", 3, "phone", member_number=1012)
    entry = journal.read_entry(state["journal"], 0)
    assert (entry["staff_code"], entry["action"], entry["booking_reference"]) == ("ST004", "NEW BOOKING", "BS-10442")
    assert operations.find_booking(state, "BS-10442")["guest_name"] == "Grace O-Brien"
