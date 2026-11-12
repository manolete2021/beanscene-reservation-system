"""IPC: inter-process communication for Bean Scene.

IPC means inter-process communication. Two separate copies of the
application run at the same time. Updates travel one way only, from
the Floor Tablet to the Reservation Desk. The copies talk with TCP
sockets on this computer.

The listener only receives a line and places it on a queue. It does
not change bookings, the journal, the undo stack, or the window.
"""

import socket
import threading

# The Desk listens on this address. The Tablet connects to it.
# 127.0.0.1 is this computer only. Nothing is sent across the network.
HOST = "127.0.0.1"
PORT = 50505

# How long a socket call may wait, in seconds. Short, so a missing Desk
# does not hold up the Tablet for long.
_TIMEOUT = 2

# The largest update line we will read. A real line is much shorter.
_MAX_LINE = 200

# Listener state. accept waits until a Tablet connects or the timeout
# ends. Closing the socket makes accept return, so the thread can finish.
_lock = threading.Lock()
_server = None
_thread = None
_stop = threading.Event()


def send_update(message):
    """Send one update line from the Floor Tablet to the Reservation Desk.

    The line is SEAT, a booking reference and a table code, or COMPLETE
    and a booking reference. One connection is opened, the line is sent
    with a newline, and the connection is closed. The Desk does not
    send a reply.

    Returns (True, note) when the line was handed to the Desk, or
    (False, note) when it was not. A failed connection is never
    reported as delivered.
    """
    # Refuse a bad line before opening a socket, so we do not claim
    # that anything was delivered.
    try:
        parse_update(message)
    except ValueError as error:
        return False, str(error)

    line = message.strip() + "\n"
    link = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    link.settimeout(_TIMEOUT)
    try:
        # If the Desk is not listening, connect raises and the Tablet
        # keeps running. The booking change on the Tablet is not undone.
        link.connect((HOST, PORT))
        link.sendall(line.encode("utf-8"))
    except OSError:
        return False, "The Reservation Desk is not running. The update was not sent."
    finally:
        # Always close, whether the send worked or the Desk was offline.
        try:
            link.close()
        except OSError:
            pass
    return True, "Update sent to the Reservation Desk."


def parse_update(message):
    """Check an update line and return its action and values.

    Allowed lines, with the words separated by spaces:

        SEAT BS-10432 A4
        COMPLETE BS-10432

    Returns a dictionary with the keys action, reference and table.
    COMPLETE uses an empty table. Raises ValueError when the line is
    empty, the action is unknown, a value is missing, or extra words
    are present.
    """
    text = message.strip()
    if text == "":
        raise ValueError("The update message is empty.")

    parts = text.split()
    action = parts[0].upper()

    # A seat needs the booking and the table. No more and no less.
    if action == "SEAT":
        if len(parts) != 3:
            raise ValueError("A seat update needs a booking reference and a table code.")
        return {"action": "SEAT", "reference": parts[1].upper(), "table": parts[2].upper()}

    # A complete needs only the booking. The Desk already knows the table.
    if action == "COMPLETE":
        if len(parts) != 2:
            raise ValueError("A complete update needs a booking reference.")
        return {"action": "COMPLETE", "reference": parts[1].upper(), "table": ""}

    raise ValueError("The update action is not SEAT or COMPLETE.")


def start_listener(incoming_queue):
    """Listen for Tablet updates and place valid ones on incoming_queue.

    The work runs in a background thread so the window thread is not
    blocked. This thread only receives and queues. It does not change
    bookings, the journal, the undo stack, or any widget. The main
    thread reads the queue later and updates the Desk.
    """
    global _server, _thread

    def accept_loop(server):
        # accept waits for a Tablet. The timeout lets the loop notice
        # stop_listener. It is not a busy loop: the thread sleeps inside
        # accept until a connection arrives or the timeout ends.
        while not _stop.is_set():
            try:
                client, _address = server.accept()
            except socket.timeout:
                continue
            except OSError:
                # stop_listener closed the listening socket.
                break
            try:
                _read_one_message(client, incoming_queue)
            finally:
                # One message per connection, then close. No reply is sent.
                try:
                    client.close()
                except OSError:
                    pass

    with _lock:
        # Starting twice would try to bind the same port.
        if _thread is not None and _thread.is_alive():
            return
        _stop.clear()
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Allow the Desk to listen again soon after a clean stop.
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((HOST, PORT))
            server.listen()
            server.settimeout(_TIMEOUT)
        except OSError:
            server.close()
            raise
        _server = server
        _thread = threading.Thread(
            target=accept_loop, args=(server,), name="beanscene-ipc", daemon=True
        )
        _thread.start()


def stop_listener():
    """Stop the background listener and close its socket.

    Safe to call more than once, and safe when the listener was never
    started. Clean shutdown calls this so the listening socket is not
    left open.
    """
    global _server, _thread
    # The accept loop sees this flag after the current wait ends.
    _stop.set()
    with _lock:
        server = _server
        _server = None
        thread = _thread
    if server is not None:
        try:
            server.close()
        except OSError:
            pass
    # Wait for the thread, but do not wait forever if it is already stuck.
    if thread is not None and thread is not threading.current_thread():
        thread.join(timeout=_TIMEOUT + 1)
    with _lock:
        if _thread is thread:
            _thread = None


def _read_one_message(client, incoming_queue):
    """Read one newline-terminated line and queue it when it is valid."""
    client.settimeout(_TIMEOUT)
    data = b""
    try:
        # Keep reading until the newline that ends this one update.
        while b"\n" not in data:
            chunk = client.recv(1024)
            # The Tablet closed the connection before the newline.
            if chunk == b"":
                return
            data += chunk
            # Drop a line that is far longer than a real update.
            if len(data) > _MAX_LINE:
                return
    except OSError:
        return

    raw = data.split(b"\n", 1)[0]
    try:
        text = raw.decode("utf-8")
    except UnicodeError:
        return
    try:
        update = parse_update(text)
    except ValueError:
        # A bad line is ignored. The listener keeps running.
        return
    # queue.Queue is safe to fill from this thread. The main thread
    # takes the item out later. Nothing here touches Tkinter.
    incoming_queue.put(update)
