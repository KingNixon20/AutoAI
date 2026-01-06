import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

import pathlib


class ProjectsView(Gtk.Box):
    def __init__(self, application):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.application = application

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        # show the actual projects folder path as the header label
        self.projects_dir = pathlib.Path.cwd() / "projects"
        title = Gtk.Label(label=str(self.projects_dir))
        title.get_style_context().add_class("title")
        header.append(title)

        # spacer pushes the button to the right
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header.append(spacer)

        # New Project button with + icon to the right
        new_btn = Gtk.Button()
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_label = Gtk.Label(label="New Project")
        # create icon without explicit size to avoid GTK version constant differences
        btn_icon = Gtk.Image.new_from_icon_name("list-add")
        btn_box.append(btn_label)
        btn_box.append(btn_icon)
        new_btn.set_child(btn_box)
        new_btn.connect("clicked", self.on_new_project)
        header.append(new_btn)

        self.append(header)

        # Separator below header spanning full width
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        sep.set_margin_top(6)
        sep.set_margin_bottom(6)
        self.append(sep)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroller.set_vexpand(True)  # Allow vertical expansion
        scroller.set_hexpand(True)  # Allow horizontal expansion

        self.flow = Gtk.FlowBox()
        self.flow.set_min_children_per_line(3)
        self.flow.set_max_children_per_line(6)
        self.flow.set_row_spacing(8)
        self.flow.set_column_spacing(8)
        self.flow.set_margin_start(12)  # Add margins around the flow
        self.flow.set_margin_end(12)
        self.flow.set_margin_top(12)
        self.flow.set_margin_bottom(12)
        self.flow.set_valign(Gtk.Align.START)  # Align to top, don't stretch

        scroller.set_child(self.flow)
        self.append(scroller)

        self.load_projects()

    def load_projects(self):
        projects_dir = self.projects_dir
        projects_dir.mkdir(exist_ok=True)

        # Clear existing children
        while True:
            child = self.flow.get_first_child()
            if child is None:
                break
            self.flow.remove(child)

        for child in projects_dir.iterdir():
            if not child.is_dir():
                continue

            btn = Gtk.Button()
            btn.set_size_request(200, 220)  # Fixed card size
            btn.set_valign(Gtk.Align.START)  # Don't stretch vertically
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            box.set_margin_start(8)
            box.set_margin_end(8)
            box.set_margin_top(8)
            box.set_margin_bottom(8)

            thumb = child / "thumbnail.png"
            if thumb.exists():
                try:
                    from gi.repository import GdkPixbuf
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        str(thumb), 180, 150, True
                    )
                    image = Gtk.Image.new_from_pixbuf(pixbuf)
                except Exception:
                    image = Gtk.Image.new_from_icon_name("folder")
                    image.set_pixel_size(128)
            else:
                image = Gtk.Image.new_from_icon_name("folder")
                image.set_pixel_size(128)

            label = Gtk.Label(label=child.name)
            label.set_wrap(True)
            label.set_max_width_chars(20)
            label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
            
            box.append(image)
            box.append(label)
            btn.set_child(box)

            # Detect double-click to open editor
            # single-click opens editor; double-click is also supported via gesture
            btn.connect("clicked", lambda b, p=child: self.open_editor(p))
            gesture = Gtk.GestureClick()
            gesture.connect("pressed", self._on_pressed, child)
            btn.add_controller(gesture)

            self.flow.append(btn)

    def on_new_project(self, button):
        dialog = Gtk.Dialog(title="Create Project", transient_for=self.get_root(), modal=True)
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_OK", Gtk.ResponseType.OK)
        
        content = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_placeholder_text("project-name")
        content.append(entry)
        
        dialog.connect("response", self._on_new_project_response, entry)
        dialog.present()

    def _on_new_project_response(self, dialog, response_id, entry):
        name = entry.get_text().strip()
        dialog.destroy()

        if response_id == Gtk.ResponseType.OK and name:
            new_dir = self.projects_dir / name
            try:
                new_dir.mkdir(parents=True, exist_ok=False)
            except FileExistsError:
                # show message
                msg = Gtk.MessageDialog(
                    transient_for=self.get_root(),
                    modal=True,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text=f"Project '{name}' already exists"
                )
                msg.connect("response", lambda d, r: d.destroy())
                msg.present()
                return

            # create workflows dir
            (new_dir / "workflows").mkdir(exist_ok=True)
            # reload UI
            self.load_projects()

    def _on_pressed(self, gesture, n_press, x, y, project_path):
        if n_press == 2:
            self.open_editor(project_path)

    def open_editor(self, project_path):
        from app.ui.editor_window import EditorWindow

        win = EditorWindow(application=self.application, project_path=project_path)
        win.present()