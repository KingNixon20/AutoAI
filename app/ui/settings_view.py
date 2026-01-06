import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class SettingsView(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        title = Gtk.Label(label="Settings")
        title.get_style_context().add_class("title")
        self.append(title)

        grid = Gtk.Grid(column_spacing=8, row_spacing=8)

        grid.attach(Gtk.Label(label="Driver Priority:"), 0, 0, 1, 1)
        self.driver_entry = Gtk.Entry()
        self.driver_entry.set_text("pyautogui,xdotool,ydotool")
        grid.attach(self.driver_entry, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Default Timeout (s):"), 0, 1, 1, 1)
        self.timeout_entry = Gtk.Entry()
        self.timeout_entry.set_text("5")
        grid.attach(self.timeout_entry, 1, 1, 1, 1)

        save_btn = Gtk.Button(label="Save Settings")
        save_btn.connect("clicked", self.on_save)
        grid.attach(save_btn, 0, 2, 2, 1)

        self.append(grid)

    def on_save(self, button):
        # Placeholder: persist settings later
        drivers = self.driver_entry.get_text()
        timeout = self.timeout_entry.get_text()
        print(f"Settings saved: drivers={drivers}, timeout={timeout}")
