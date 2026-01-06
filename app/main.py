#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk

from app.ui.main_window import MainWindow


def main():
    app = Gtk.Application(application_id="com.autoai.app")

    # Load application CSS to show selected thumbnails and style save button
    css = b"""
button.selected {
  border: 2px solid #4A90E2;
  border-radius: 4px;
}
button.save-button {
  background-color: #2ecc71;
  color: #ffffff;
  border-radius: 6px;
  padding: 6px;
}
button.save-button image {
  margin: 0px;
}
button.delete-button {
  background-color: #e74c3c;
  color: #ffffff;
  border-radius: 6px;
  padding: 6px;
}
button.delete-button image {
  margin: 0px;
}
button.undo-button {
  background-color: #3498db;
  color: #ffffff;
  border-radius: 6px;
  padding: 6px;
}
button.undo-button image {
  margin: 0px;
}
"""

    provider = Gtk.CssProvider()
    try:
        provider.load_from_data(css)
        display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    except Exception:
        pass

    def on_activate(app):
        win = MainWindow(application=app)
        win.present()

    app.connect("activate", on_activate)
    return app.run(None)


if __name__ == "__main__":
    main()

#
