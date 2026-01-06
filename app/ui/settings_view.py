import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

import yaml
from pathlib import Path
import os


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

        # Projects directory setting
        grid.attach(Gtk.Label(label="Projects Dir:"), 0, 2, 1, 1)
        self.projects_entry = Gtk.Entry()
        # use central config helper if available
        try:
            from app.config import get_projects_dir
            self.projects_entry.set_text(str(get_projects_dir()))
        except Exception:
            self.projects_entry.set_text(str(Path.cwd() / "projects"))
        grid.attach(self.projects_entry, 1, 2, 1, 1)
        browse_btn = Gtk.Button(label="Browse")
        browse_btn.connect("clicked", self.on_browse_projects)
        grid.attach(browse_btn, 2, 2, 1, 1)

        save_btn = Gtk.Button(label="Save Settings")
        save_btn.connect("clicked", self.on_save)
        grid.attach(save_btn, 0, 3, 3, 1)

        self.append(grid)

        # try load existing config
        self._config_path = Path.home() / '.config' / 'autoai' / 'config.yaml'
        try:
            if self._config_path.exists():
                with open(self._config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                drivers = data.get('drivers')
                timeout = data.get('timeout')
                projects = data.get('projects_dir')
                if drivers:
                    self.driver_entry.set_text(drivers)
                if timeout:
                    self.timeout_entry.set_text(str(timeout))
                if projects:
                    self.projects_entry.set_text(str(projects))
        except Exception:
            pass

    def on_save(self, button):
        drivers = self.driver_entry.get_text().strip()
        timeout = self.timeout_entry.get_text().strip()
        projects_dir = self.projects_entry.get_text().strip()

        # persist using app.config helper
        try:
            from app.config import save_config
            save_config({'drivers': drivers, 'timeout': timeout, 'projects_dir': projects_dir})
        except Exception:
            try:
                # fallback to local write
                self._config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self._config_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump({
                        'drivers': drivers,
                        'timeout': timeout,
                        'projects_dir': projects_dir,
                    }, f)
            except Exception as e:
                print(f"Failed to save settings: {e}")

        print(f"Settings saved: drivers={drivers}, timeout={timeout}, projects_dir={projects_dir}")

    def on_browse_projects(self, button):
        dialog = Gtk.FileChooserNative(title="Select Projects Directory", transient_for=self.get_root(), action=Gtk.FileChooserAction.SELECT_FOLDER)
        resp = dialog.run()
        if resp == Gtk.ResponseType.OK:
            try:
                folder = dialog.get_file().get_path()
                # update entry
                self.projects_entry.set_text(str(folder))
            except Exception:
                pass
        dialog.destroy()

#
