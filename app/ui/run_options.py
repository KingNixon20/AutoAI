import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class RunOptions(Gtk.Frame):
    """Widget exposing run options: loop, loop count/infinite, and delay settings."""

    def __init__(self):
        super().__init__(label="Run Options")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)
        self.set_child(box)

        self.chk_loop = Gtk.CheckButton(label="Loop workflow")
        self.chk_loop.set_tooltip_text("Repeat the whole workflow when finished")
        box.append(self.chk_loop)

        loop_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        loop_row.append(Gtk.Label(label="Times:"))
        adjustment = Gtk.Adjustment(value=1, lower=1, upper=1000000, step_increment=1)
        self.spin_loops = Gtk.SpinButton(adjustment=adjustment, climb_rate=1, digits=0)
        self.spin_loops.set_tooltip_text("Number of times to loop (ignored if Infinite is checked)")
        loop_row.append(self.spin_loops)
        self.chk_infinite = Gtk.CheckButton(label="Infinite")
        self.chk_infinite.connect("toggled", self._on_infinite_toggled)
        loop_row.append(self.chk_infinite)
        box.append(loop_row)

        box.append(Gtk.Label(label="Delay between steps (seconds):"))

        self.chk_random_delay = Gtk.CheckButton(label="Use random delay range")
        self.chk_random_delay.connect("toggled", self._on_random_toggled)
        box.append(self.chk_random_delay)

        delay_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        adj_delay = Gtk.Adjustment(value=0.5, lower=0.0, upper=3600.0, step_increment=0.1)
        self.spin_delay = Gtk.SpinButton(adjustment=adj_delay, climb_rate=0.1, digits=2)
        self.spin_delay.set_tooltip_text("Fixed delay between steps in seconds")
        delay_row.append(self.spin_delay)

        adj_min = Gtk.Adjustment(value=0.2, lower=0.0, upper=3600.0, step_increment=0.1)
        self.spin_delay_min = Gtk.SpinButton(adjustment=adj_min, climb_rate=0.1, digits=2)
        self.spin_delay_min.set_tooltip_text("Random delay minimum")
        self.spin_delay_min.set_sensitive(False)
        adj_max = Gtk.Adjustment(value=1.0, lower=0.0, upper=3600.0, step_increment=0.1)
        self.spin_delay_max = Gtk.SpinButton(adjustment=adj_max, climb_rate=0.1, digits=2)
        self.spin_delay_max.set_tooltip_text("Random delay maximum")
        self.spin_delay_max.set_sensitive(False)
        delay_row.append(Gtk.Label(label="Min:"))
        delay_row.append(self.spin_delay_min)
        delay_row.append(Gtk.Label(label="Max:"))
        delay_row.append(self.spin_delay_max)
        box.append(delay_row)

        spacer = Gtk.Box()
        try:
            spacer.set_vexpand(True)
        except Exception:
            pass
        box.append(spacer)

        # wire signals
        self.chk_loop.connect('toggled', lambda w: None)
        self.spin_loops.connect('value-changed', lambda w: None)
        self.chk_infinite.connect('toggled', lambda w: None)
        self.chk_random_delay.connect('toggled', lambda w: None)
        self.spin_delay.connect('value-changed', lambda w: None)
        self.spin_delay_min.connect('value-changed', lambda w: None)
        self.spin_delay_max.connect('value-changed', lambda w: None)

    def _on_infinite_toggled(self, widget):
        inf = bool(self.chk_infinite.get_active())
        try:
            self.spin_loops.set_sensitive(not inf)
        except Exception:
            pass

    def _on_random_toggled(self, widget):
        rand = bool(self.chk_random_delay.get_active())
        try:
            self.spin_delay.set_sensitive(not rand)
            self.spin_delay_min.set_sensitive(rand)
            self.spin_delay_max.set_sensitive(rand)
        except Exception:
            pass

    def get_settings(self):
        return {
            'loop': bool(self.chk_loop.get_active()),
            'infinite': bool(self.chk_infinite.get_active()),
            'loop_count': int(self.spin_loops.get_value()),
            'delay_mode': 'random' if bool(self.chk_random_delay.get_active()) else 'fixed',
            'delay': float(self.spin_delay.get_value()),
            'delay_min': float(self.spin_delay_min.get_value()),
            'delay_max': float(self.spin_delay_max.get_value()),
        }

    def set_settings(self, settings: dict):
        try:
            if 'loop' in settings:
                self.chk_loop.set_active(bool(settings.get('loop', False)))
            if 'infinite' in settings:
                self.chk_infinite.set_active(bool(settings.get('infinite', False)))
            if 'loop_count' in settings:
                self.spin_loops.set_value(int(settings.get('loop_count', 1)))
            if 'delay_mode' in settings:
                self.chk_random_delay.set_active(settings.get('delay_mode') == 'random')
            if 'delay' in settings:
                self.spin_delay.set_value(float(settings.get('delay', 0.5)))
            if 'delay_min' in settings:
                self.spin_delay_min.set_value(float(settings.get('delay_min', 0.2)))
            if 'delay_max' in settings:
                self.spin_delay_max.set_value(float(settings.get('delay_max', 1.0)))
        except Exception:
            pass
        self._on_infinite_toggled(None)
        self._on_random_toggled(None)
