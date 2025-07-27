#!/usr/bin/env python3
import gi
import os

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from ui.main_window import BropadWindow

if __name__ == "__main__":
    app = Gtk.Application(application_id="com.bropad.app")

    def on_activate(app):
        win = BropadWindow(app)
        win.show_all()

    app.connect("activate", on_activate)
    app.run(None)
