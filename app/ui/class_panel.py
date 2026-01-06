import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

import pathlib
from typing import Callable, Optional


class ClassPanel(Gtk.Box):
    """Panel for managing PyAutoGUI image classes."""
    
    def __init__(self, project_path: pathlib.Path, on_classes_changed: Optional[Callable] = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.project_path = pathlib.Path(project_path)
        self.classes_dir = self.project_path / "classes"
        self.classes_dir.mkdir(parents=True, exist_ok=True)
        self.on_classes_changed = on_classes_changed

        # Header with title and create button
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        title = Gtk.Label(label="Image Classes")
        title.get_style_context().add_class("title-4")
        title.set_halign(Gtk.Align.START)
        header.append(title)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header.append(spacer)
        
        create_btn = Gtk.Button(label="Create Class")
        create_btn.connect("clicked", self.on_create)
        header.append(create_btn)
        
        self.append(header)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(sep)

        # List of classes
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.get_style_context().add_class("boxed-list")
        
        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)
        scroller.set_child(self.listbox)
        self.append(scroller)

        # Action buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        button_box.set_halign(Gtk.Align.END)
        
        delete_btn = Gtk.Button(label="Delete Selected")
        delete_btn.get_style_context().add_class("destructive-action")
        delete_btn.connect("clicked", self.on_delete)
        button_box.append(delete_btn)
        
        self.append(button_box)

        self.load()

    def load(self):
        """Load and display all classes from the classes directory."""
        # Clear existing items
        while True:
            child = self.listbox.get_first_child()
            if child is None:
                break
            self.listbox.remove(child)

        # Add classes
        for d in sorted(self.classes_dir.iterdir()):
            if not d.is_dir():
                continue
            
            # Create row with class name
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row_box.set_margin_start(12)
            row_box.set_margin_end(12)
            row_box.set_margin_top(8)
            row_box.set_margin_bottom(8)
            
            # Icon
            icon = Gtk.Image.new_from_icon_name("folder")
            icon.set_pixel_size(24)
            row_box.append(icon)
            
            # Label
            label = Gtk.Label(label=d.name)
            label.set_halign(Gtk.Align.START)
            label.set_hexpand(True)
            row_box.append(label)
            
            # Image count
            image_count = len(list(d.glob("*.png")))
            count_label = Gtk.Label(label=f"{image_count} images")
            count_label.get_style_context().add_class("dim-label")
            row_box.append(count_label)
            
            row = Gtk.ListBoxRow()
            row.set_child(row_box)
            row.class_name = d.name  # Store class name for deletion
            self.listbox.append(row)
        
        # Notify that classes have changed
        if self.on_classes_changed:
            self.on_classes_changed()

    def on_create(self, button):
        """Create a new class directory."""
        dialog = Gtk.Dialog(title="Create Class", transient_for=self.get_root(), modal=True)
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Create", Gtk.ResponseType.OK)
        
        content = dialog.get_content_area()
        content.set_margin_start(12)
        content.set_margin_end(12)
        content.set_margin_top(12)
        content.set_margin_bottom(12)
        
        label = Gtk.Label(label="Enter class name:")
        label.set_halign(Gtk.Align.START)
        content.append(label)
        
        entry = Gtk.Entry()
        entry.set_placeholder_text("button-login")
        content.append(entry)
        
        dialog.connect("response", self._on_create_response, entry)
        dialog.present()

    def _on_create_response(self, dialog, response_id, entry):
        """Handle create class dialog response."""
        name = entry.get_text().strip()
        dialog.destroy()

        if response_id == Gtk.ResponseType.OK and name:
            new_dir = self.classes_dir / name
            try:
                new_dir.mkdir(parents=True, exist_ok=False)
                self.load()
            except FileExistsError:
                msg = Gtk.MessageDialog(
                    transient_for=self.get_root(),
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text=f"Class '{name}' already exists"
                )
                msg.connect("response", lambda d, r: d.destroy())
                msg.present()

    def on_delete(self, button):
        """Delete the selected class."""
        selected_row = self.listbox.get_selected_row()
        if not selected_row:
            return
        
        class_name = selected_row.class_name
        
        # Confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.get_root(),
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f"Delete class '{class_name}'?"
        )
        dialog.format_secondary_text(
            "This will permanently delete the class directory and all its images."
        )
        dialog.connect("response", self._on_delete_response, class_name)
        dialog.present()

    def _on_delete_response(self, dialog, response_id, class_name):
        """Handle delete confirmation response."""
        dialog.destroy()
        
        if response_id == Gtk.ResponseType.OK:
            import shutil
            class_dir = self.classes_dir / class_name
            try:
                shutil.rmtree(class_dir)
                self.load()
            except Exception as e:
                msg = Gtk.MessageDialog(
                    transient_for=self.get_root(),
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text=f"Failed to delete class: {e}"
                )
                msg.connect("response", lambda d, r: d.destroy())
                msg.present()

    def list_classes(self):
        """Return list of all class names."""
        classes = []
        child = self.listbox.get_first_child()
        while child:
            if hasattr(child, 'class_name'):
                classes.append(child.class_name)
            child = child.get_next_sibling()
        return classes