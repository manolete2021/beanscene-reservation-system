"""Booking index: a hash table with chaining, built by hand.

* Hash: add up the character codes of the booking reference, then take the
  remainder after dividing by the number of buckets.
* Buckets: a fixed number from config.json (16).
* Collisions: each bucket is a list; a new booking goes on the end.
* Operations: add and find. There is no delete, because a booking is
  cancelled rather than removed.
"""


def hash_reference(reference, bucket_count):
    """Return the bucket number for a booking reference.

    BS-10432: B(66) + S(83) + -(45) + 1(49) + 0(48) + 4(52) + 3(51) + 2(50)
    = 444, and 444 mod 16 = 12, so it goes in bucket 12.
    """
    total = 0
    for character in reference:
        total = total + ord(character)
    return total % bucket_count


def explain_hash(reference, bucket_count):
    """Show the hash working step by step, e.g. for BS-10432."""
    working = ""
    total = 0
    for character in reference:
        if working != "":
            working = working + " + "
        working = working + f"{character}({ord(character)})"
        total = total + ord(character)
    return f"{working} = {total}; {total} mod {bucket_count} = {total % bucket_count}"


def new_index(bucket_count):
    """Return an empty index with bucket_count empty buckets."""
    buckets = []
    for number in range(bucket_count):
        buckets.append([])
    return {"bucket_count": bucket_count, "buckets": buckets, "size": 0}


def index_add(index, booking):
    """Add a booking to the end of its bucket and return the bucket number."""
    if index_find(index, booking["reference"]) is not None:
        raise ValueError(f"Booking {booking['reference']} already exists.")
    bucket_number = hash_reference(booking["reference"], index["bucket_count"])
    index["buckets"][bucket_number].append(booking)
    index["size"] = index["size"] + 1
    return bucket_number


def index_find(index, reference):
    """Find a booking by its reference, looking only in the bucket it hashes to."""
    reference = reference.strip().upper()
    bucket_number = hash_reference(reference, index["bucket_count"])
    for booking in index["buckets"][bucket_number]:
        if booking["reference"] == reference:
            return booking
    return None


def all_bookings(index):
    """Return every booking, sorted by reference (for listing them)."""
    references = []
    for bucket in index["buckets"]:
        for booking in bucket:
            references.append(booking["reference"])
    references.sort()
    bookings = []
    for reference in references:
        bookings.append(index_find(index, reference))
    return bookings


def bucket_sizes(index):
    """How many bookings are in each bucket - shows the chaining."""
    sizes = []
    for bucket in index["buckets"]:
        sizes.append(len(bucket))
    return sizes
