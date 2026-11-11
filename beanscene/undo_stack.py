"""Undo stack: last in, first out.

Every change is pushed onto the stack; Undo pops the most recent one off.
A Python list holds the items. The end of the list is the top of the stack.
"""


def new_stack():
    """Return an empty stack."""
    return []


def push(stack, item):
    """Put an item on top of the stack."""
    stack.append(item)


def pop(stack):
    """Take the top item off the stack and return it."""
    if len(stack) == 0:
        raise ValueError("There is nothing to undo.")
    return stack.pop()


def peek(stack):
    """Return the top item without taking it off, or None if the stack is empty."""
    if len(stack) == 0:
        return None
    return stack[-1]
