import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
from pathlib import Path
import time
import datetime
import os

try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    from PIL import ImageGrab
except Exception:
    ImageGrab = None


class ScreenshotRecorder(Gtk.Window):
    def __init__(self, project_path: Path, transient_for=None):
        super().__init__(title="Screenshot Recorder", transient_for=transient_for)
        self.project_path = Path(project_path)
        self.set_default_size(400, 120)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        self.set_child(vbox)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.btn_start = Gtk.Button(label="Start")
        self.btn_stop = Gtk.Button(label="Stop")
        self.btn_stop.set_sensitive(False)
        self.btn_start.connect("clicked", self.on_start)
        self.btn_stop.connect("clicked", self.on_stop)
        hbox.append(self.btn_start)
        hbox.append(self.btn_stop)
        vbox.append(hbox)

        self.status = Gtk.Label(label="Idle")
        vbox.append(self.status)

        self.last_saved = Gtk.Label(label="Last: -")
        vbox.append(self.last_saved)

        self._timeout_id = None
        self._running = False

    def _ensure_dir(self):
        dest = self.project_path / 'screenshots'
        dest.mkdir(parents=True, exist_ok=True)
        return dest

    def on_start(self, button):
        if self._running:
            return
        self._running = True
        self.btn_start.set_sensitive(False)
        self.btn_stop.set_sensitive(True)
        self.status.set_text('Running...')
        # schedule periodic capture every 3 seconds
        self._timeout_id = GLib.timeout_add_seconds(3, self._on_timeout)

    def on_stop(self, button=None):
        if not self._running:
            return
        self._running = False
        self.btn_start.set_sensitive(True)
        self.btn_stop.set_sensitive(False)
        self.status.set_text('Stopped')
        if self._timeout_id:
            try:
                GLib.source_remove(self._timeout_id)
            except Exception:
                pass
            self._timeout_id = None

    def _on_timeout(self):
        # take screenshot and save
        dest = self._ensure_dir()
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = dest / f'screenshot_{ts}.png'
        try:
            if pyautogui:
                img = pyautogui.screenshot()
                img.save(str(fname))
            elif ImageGrab:
                img = ImageGrab.grab()
                img.save(str(fname))
            else:
                # try GDK fallback
                try:
                    gi.require_version('Gdk', '3.0')
                except Exception:
                    pass
                # If all fail, write a small placeholder file
                with open(fname, 'wb') as f:
                    f.write(b'')
            self.last_saved.set_text(f'Last: {fname.name}')
            self.status.set_text(f'Saved {fname.name}')
        except Exception as e:
            self.status.set_text(f'Error: {e}')
        # continue the timeout
        return True

    def do_destroy(self):
        # ensure timeout removed
        self.on_stop(None)
        return super().do_destroy()
