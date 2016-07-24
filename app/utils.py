"""Useful utility functions."""

import threading

from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.popup import Popup

Builder.load_file('utils.kv')


class MyPopup(Popup):
    """Customized Popup widget used mainly for displaying errors."""

    text = StringProperty('')


def thread(task, args=()):
    # type: (function, tuple)
    """Start this task in a separate thread.

    Args:
        task: The task to be run
        args: Parameters which should be passed to this task
    """
    t = threading.Thread(target=task, args=args)
    t.daemon = True
    t.start()


def popup(text, header="Error", callback=None):
    # type: (str, str, function)
    """Display a message to the user in the form of a popup.

    Args:
        text: Text of the displayed message
        header: Heading of the displayed message
        callback: A function to be called when the popup is closed
    """
    popup_ = MyPopup(title=header)
    popup_.text = text
    popup_.open()

    if callback is not None:
        popup_.bind(on_dismiss=callback)
