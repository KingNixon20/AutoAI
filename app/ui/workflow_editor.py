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
#
