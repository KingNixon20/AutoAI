import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class WorkflowEditor(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        remove_btn = Gtk.Button(label="Remove Selected")
        remove_btn.connect("clicked", self.on_remove)
        toolbar.append(remove_btn)
        self.append(toolbar)

        self.liststore = Gtk.ListStore(str, str)
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
        params = step.get("params", {})
        
        # Format params as readable string
        params_str = ", ".join(f"{k}={v}" for k, v in params.items())
        
        self.liststore.append([step_type, params_str])

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
            params_raw = row[1] or ""
            params = {}
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