"""Journal: every change is written as a 60-byte record to a binary file.

Record layout (Table 3 of the assessment):

    field              bytes  starts at
    entry number         4      0
    timestamp           19      4     "yyyy-MM-dd HH:mm:ss"
    staff code           6     23     padded with spaces
    action              20     29     padded with spaces
    booking reference   10     49     padded with spaces
    cancelled flag       1     59     0 or 1

Record n starts at byte n x 60, so any record can be read or changed by
jumping straight to it, without touching the others. Records are never
deleted; undo only sets the cancelled flag.
"""

import struct
from datetime import datetime

from beanscene.records import make_journal_entry

RECORD_FORMAT = "<i19s6s20s10sB"
RECORD_SIZE = 60
FLAG_POSITION = 59


def pad(text, length):
    """Turn text into exactly length bytes: cut it short, or add spaces."""
    data = text.encode("ascii")[:length]
    return data.ljust(length, b" ")


def pack_entry(entry):
    """Turn a journal entry record into 60 bytes."""
    if entry["cancelled"]:
        flag = 1
    else:
        flag = 0
    return struct.pack(RECORD_FORMAT, entry["entry_number"], pad(entry["timestamp"], 19),
                       pad(entry["staff_code"], 6), pad(entry["action"], 20),
                       pad(entry["booking_reference"], 10), flag)


def unpack_entry(data):
    """Turn 60 bytes back into a journal entry record."""
    number, timestamp, staff, action, reference, flag = struct.unpack(RECORD_FORMAT, data)
    return make_journal_entry(number, timestamp.decode("ascii").strip(), staff.decode("ascii").strip(),
                              action.decode("ascii").strip(), reference.decode("ascii").strip(), flag == 1)


def open_journal(path):
    """Open the journal file for reading and writing, creating it if needed.

    Returns a dictionary holding the path and the open file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()
    return {"path": path, "file": open(path, "r+b")}


def entry_count(journal):
    """How many records are in the file: the file size divided by 60."""
    return journal["path"].stat().st_size // RECORD_SIZE


def append_entry(journal, staff_code, action, booking_reference):
    """Write a new record at the end of the file and return it."""
    number = entry_count(journal)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = make_journal_entry(number, timestamp, staff_code, action, booking_reference, False)
    journal["file"].seek(number * RECORD_SIZE)
    journal["file"].write(pack_entry(entry))
    journal["file"].flush()
    return entry


def read_entry(journal, number):
    """Read record number n by jumping straight to byte n x 60."""
    if number < 0 or number >= entry_count(journal):
        raise ValueError(f"There is no journal entry number {number}.")
    journal["file"].seek(number * RECORD_SIZE)
    return unpack_entry(journal["file"].read(RECORD_SIZE))


def read_recent(journal, limit):
    """Return up to limit of the newest records, newest first."""
    entries = []
    number = entry_count(journal) - 1
    while number >= 0 and len(entries) < limit:
        entries.append(read_entry(journal, number))
        number = number - 1
    return entries


def set_cancelled(journal, number):
    """Set the cancelled flag of record n: one byte at (n x 60) + 59. Nothing else changes."""
    if number < 0 or number >= entry_count(journal):
        raise ValueError(f"There is no journal entry number {number}.")
    journal["file"].seek(number * RECORD_SIZE + FLAG_POSITION)
    journal["file"].write(b"\x01")
    journal["file"].flush()


def close_journal(journal):
    """Close the journal file. Safe to call more than once."""
    if not journal["file"].closed:
        journal["file"].close()
