"""
A simple, text based, TBG chat client.
It's pretty jank, since it's meant only for testing.
"""

import curses  # Unix only, sorry
from getpass import getpass
from threading import Thread, Event
from queue import Queue, Empty as QueueEmpty
from time import sleep
from tbgclient import Session
from tbgclient.chat import ChatConnection

username = input("Username: ")
password = getpass("Password: ")

session = Session()
session.login(username, password)

MAX_QUEUE_SIZE = 100
quitted = Event()
new_message = Event()
message_inbox = []
message_outbox = Queue()

chat = ChatConnection(session)


def process_messages():
    while not quitted.is_set():
        chat.poll()
        message_inbox.extend(
            new_message.set()
            or f"{msg.user.name:>16}"  # all names are cropped to this size
            " │ "
            f"{msg.content}"
            for msg in chat.messages()
        )
        while len(message_inbox) > MAX_QUEUE_SIZE:
            message_inbox.pop(0)

        while not message_outbox.empty():
            try:
                msg = message_outbox.get_nowait()
                chat.send(msg)
                if msg.lower() == "/quit":
                    quitted.set()
                    break
                message_outbox.task_done()
            except QueueEmpty:
                break

        sleep(1)


msg_thread = Thread(target=process_messages, name="poll")


def display(stdscr):
    # Based from this example: https://stackoverflow.com/a/73186009
    stdscr.erase()
    stdscr.refresh()
    stdscr.nodelay(True)
    curses.raw()

    key = -1
    typed = ""

    while not quitted.is_set():
        # Brute force our way to an optimal chat preview
        if new_message.is_set():
            for i in range(MAX_QUEUE_SIZE):
                stdscr.erase()
                try:
                    stdscr.addstr(1, 0, "\n".join(message_inbox[i:]))
                except curses.error:
                    pass
                else:
                    break
            new_message.clear()

        stdscr.addstr(0, 0, "> ")
        if key == 263:  # Backspace
            typed = typed[:-1]
        elif key == 3:  # Ctrl+C
            typed = ""
        elif key == ord("\n"):  # New line
            message_outbox.put(typed)
            if typed.lower() == "/quit":
                break
            typed = ""
        elif key > 0:  # regular chars
            typed += chr(key)
        stdscr.addstr(0, 2, typed)

        key = stdscr.getch()
        sleep(0.01)


msg_thread.start()
try:
    curses.wrapper(display)
except Exception:
    quitted.set()
    raise
finally:
    if msg_thread.is_alive:
        print("Waiting until the message handler quits...")
