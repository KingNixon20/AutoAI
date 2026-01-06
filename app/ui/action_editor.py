import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

import pathlib


class ActionEditor(Gtk.Box):
    """Right-side action settings panel.

    Use `set_action_type(type_name)` to change which params are shown, and
    `get_params()` to retrieve current parameters for the selected action.
    """
    
    # Common keyboard keys
    KEYBOARD_KEYS = [
        # Letters
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
        "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
        # Numbers
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
        # Function keys
        "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
        # Special keys
        "Return", "Enter", "Tab", "Space", "Backspace", "Delete", "Escape",
        "Up", "Down", "Left", "Right",
        "Home", "End", "Page_Up", "Page_Down",
        "Insert", "Print", "Pause",
        # Modifiers
        "Shift_L", "Shift_R", "Control_L", "Control_R",
        "Alt_L", "Alt_R", "Super_L", "Super_R",
        "Caps_Lock", "Num_Lock", "Scroll_Lock",
        # Symbols
        "minus", "equal", "bracketleft", "bracketright",
        "semicolon", "apostrophe", "grave", "backslash",
        "comma", "period", "slash",
        # Numpad
        "KP_0", "KP_1", "KP_2", "KP_3", "KP_4",
        "KP_5", "KP_6", "KP_7", "KP_8", "KP_9",
        "KP_Decimal", "KP_Divide", "KP_Multiply",
        "KP_Subtract", "KP_Add", "KP_Enter",
    ]
    
    def __init__(self, project_path: pathlib.Path):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.project_path = pathlib.Path(project_path)

        header = Gtk.Label(label="Action Parameters")
        header.get_style_context().add_class("title-4")
        header.set_halign(Gtk.Align.START)
        self.append(header)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(sep)

        # params container
        self.params_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.append(self.params_box)

        # Create parameter widgets (reused across action types)
        self.delay_spin = Gtk.SpinButton.new_with_range(0, 60, 0.1)
        self.delay_spin.set_digits(2)
        self.delay_spin.set_value(1.0)
        
        self.type_entry = Gtk.Entry()
        self.type_entry.set_placeholder_text("Enter text to type")
        
        # Searchable key dropdown
        self.key_combo = Gtk.ComboBoxText(has_entry=True)
        for key in sorted(self.KEYBOARD_KEYS):
            self.key_combo.append_text(key)
        self.key_combo.set_active(0)
        
        self.retries_spin = Gtk.SpinButton.new_with_range(0, 10, 1)
        self.retries_spin.set_value(3)
        
        self.class_combo = Gtk.ComboBoxText()

        # current action type
        self.current_type = None

    def set_action_type(self, typ: str):
        """Update the parameters panel based on action type."""
        self.current_type = typ
        
        # Clear existing parameters
        while True:
            child = self.params_box.get_first_child()
            if child is None:
                break
            self.params_box.remove(child)

        if typ == "Delay":
            self._add_param_row("Delay (seconds):", self.delay_spin)
            
        elif typ == "FindAndClick":
            self._reload_classes()
            self._add_param_row("Class Name:", self.class_combo)
            self._add_param_row("Max Retries:", self.retries_spin)
            
        elif typ == "TypeText":
            self._add_param_row("Text to Type:", self.type_entry)
            
        elif typ == "KeyPress":
            self._add_param_row("Key Name:", self.key_combo)
            help_label = Gtk.Label(label="Type to search or select from list")
            help_label.set_halign(Gtk.Align.START)
            help_label.get_style_context().add_class("dim-label")
            help_label.set_wrap(True)
            self.params_box.append(help_label)

    def _add_param_row(self, label_text: str, widget: Gtk.Widget):
        """Helper to add a label + widget row."""
        row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        label = Gtk.Label(label=label_text)
        label.set_halign(Gtk.Align.START)
        row.append(label)
        
        widget.set_hexpand(True)
        row.append(widget)
        
        self.params_box.append(row)

    def _reload_classes(self):
        """Populate class dropdown from project's classes directory."""
        self.class_combo.remove_all()
        classes_dir = self.project_path / "classes"
        
        if classes_dir.exists():
            for d in sorted(classes_dir.iterdir()):
                if d.is_dir():
                    self.class_combo.append_text(d.name)
        
        # Set first item active if available
        if self.class_combo.get_model():
            iter_first = self.class_combo.get_model().get_iter_first()
            if iter_first:
                self.class_combo.set_active(0)

    def get_params(self) -> dict:
        """Get current parameter values as a dictionary."""
        typ = self.current_type
        params = {}
        
        if typ == "Delay":
            params["seconds"] = float(self.delay_spin.get_value())
            
        elif typ == "FindAndClick":
            params["class"] = self.class_combo.get_active_text() or ""
            params["retries"] = int(self.retries_spin.get_value())
            
        elif typ == "TypeText":
            params["text"] = self.type_entry.get_text()
            
        elif typ == "KeyPress":
            # Get text from entry (supports both typed and selected values)
            key_entry = self.key_combo.get_child()
            params["key"] = key_entry.get_text() if key_entry else ""
            
        return params

    def reload_classes_if_needed(self):
        """Public method to refresh class list from disk."""
        self._reload_classes()
#
