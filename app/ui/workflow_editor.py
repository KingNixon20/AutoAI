import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
import json


class WorkflowEditor(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        remove_btn = Gtk.Button(label="Remove Selected")
        remove_btn.connect("clicked", self.on_remove)
        toolbar.append(remove_btn)
        self.append(toolbar)

        # columns: 0=type, 1=display string, 2=params json (hidden)
        self.liststore = Gtk.ListStore(str, str, str)
        self.tree = Gtk.TreeView(model=self.liststore)
        self.tree.set_vexpand(True)

        renderer_text = Gtk.CellRendererText()
        col1 = Gtk.TreeViewColumn("Action Type", renderer_text, text=0)
        col2 = Gtk.TreeViewColumn("Parameters", renderer_text, text=1)
        col1.set_resizable(True)
        col2.set_resizable(True)
        self.tree.append_column(col1)
        self.tree.append_column(col2)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        scroller.set_child(self.tree)
        self.append(scroller)

    def add_step(self, step: dict):
        """Add a step to the workflow.
        
        Args:
            step: dict with 'type' and 'params' keys
        """
        step_type = step.get("type", "Unknown")
        params = step.get("params", {}) or {}

        # Format params as readable string for display
        try:
            params_str = ", ".join(f"{k}={v}" for k, v in params.items())
        except Exception:
            params_str = str(params)

        # Serialize params to JSON for exact round-trip (fallback to str for non-serializables)
        try:
            params_json = json.dumps(params, ensure_ascii=False, default=str)
        except Exception:
            params_json = json.dumps({k: str(v) for k, v in (params.items() if isinstance(params, dict) else [])})

        self.liststore.append([step_type, params_str, params_json])

    def on_remove(self, button):
        selection = self.tree.get_selection()
        model, treeiter = selection.get_selected()
        if treeiter:
            model.remove(treeiter)

    def get_steps(self):
        """Return the list of steps as dicts: {'type':..., 'params': {...}}"""
        out = []
        for row in self.liststore:
            step_type = row[0]
            params_json = row[2] or ""
            params = {}
            if params_json:
                try:
                    params = json.loads(params_json)
                except Exception:
                    params = {}
            else:
                # fallback to parsing the display string (legacy support)
                params_raw = row[1] or ""
                for part in params_raw.split(","):
                    if not part.strip():
                        continue
                    if "=" in part:
                        k, v = part.split("=", 1)
                        params[k.strip()] = v.strip()
                    else:
                        params[part.strip()] = True

            out.append({"type": step_type, "params": params})
        return out

    def clear_steps(self):
        """Remove all steps from the editor."""
        # Clear the ListStore safely
        self.liststore.clear()

    # --- Options panel helpers ---
    def _on_infinite_toggled(self, widget):
        inf = bool(self.chk_infinite.get_active())
        try:
            self.spin_loops.set_sensitive(not inf)
        except Exception:
            pass
        self._update_settings()

    def _on_random_toggled(self, widget):
        rand = bool(self.chk_random_delay.get_active())
        try:
            self.spin_delay.set_sensitive(not rand)
            self.spin_delay_min.set_sensitive(rand)
            self.spin_delay_max.set_sensitive(rand)
        except Exception:
            pass
        self._update_settings()

    def _update_settings(self):
        self._settings['loop'] = bool(self.chk_loop.get_active())
        self._settings['infinite'] = bool(self.chk_infinite.get_active())
        try:
            self._settings['loop_count'] = int(self.spin_loops.get_value())
        except Exception:
            self._settings['loop_count'] = 1
        self._settings['delay_mode'] = 'random' if bool(self.chk_random_delay.get_active()) else 'fixed'
        try:
            self._settings['delay'] = float(self.spin_delay.get_value())
            self._settings['delay_min'] = float(self.spin_delay_min.get_value())
            self._settings['delay_max'] = float(self.spin_delay_max.get_value())
        except Exception:
            pass

    def get_settings(self):
        """Return current run options as a dict.

        Keys: `loop` (bool), `infinite` (bool), `loop_count` (int),
        `delay_mode` ('fixed'|'random'), `delay`, `delay_min`, `delay_max`.
        """
        # ensure state reflects current widgets
        self._update_settings()
        return dict(self._settings)

    def set_settings(self, settings: dict):
        """Apply settings dict to the options UI (partial allowed)."""
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
        # update dependent widget sensitivity
        self._on_infinite_toggled(None)
        self._on_random_toggled(None)
#
