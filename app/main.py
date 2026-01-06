#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from app.ui.main_window import MainWindow


def main():
    app = Gtk.Application(application_id="com.autoai.app")

    def on_activate(app):
        win = MainWindow(application=app)
        win.present()

    app.connect("activate", on_activate)
    return app.run(None)


if __name__ == "__main__":
    main()

#
