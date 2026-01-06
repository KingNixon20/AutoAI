import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

import pathlib
import shutil
import subprocess
import sys
from pathlib import Path


class ImageTemplates(Gtk.Box):
    """Tab to manage image templates assigned to classes."""

    def __init__(self, project_path: pathlib.Path):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.project_path = pathlib.Path(project_path)
        self.classes_dir = self.project_path / "classes"

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.append(Gtk.Label(label="Image Templates"))
        self.append(header)

        # Class selector
        selector = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        selector.append(Gtk.Label(label="Class:"))
        self.class_combo = Gtk.ComboBoxText()
        selector.append(self.class_combo)
        refresh_btn = Gtk.Button(label="Refresh Classes")
        refresh_btn.connect("clicked", lambda *_: self.reload_classes())
        selector.append(refresh_btn)
        self.append(selector)

        # Flow of thumbnails
        self.flow = Gtk.FlowBox()
        self.flow.set_min_children_per_line(4)
        scroller = Gtk.ScrolledWindow()
        scroller.set_child(self.flow)
        scroller.set_vexpand(True)
        self.append(scroller)

        # Buttons: Add Image, Delete Selected
        btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        add_btn = Gtk.Button(label="Add Image")
        add_btn.connect("clicked", self.on_add_image)
        btns.append(add_btn)
        labeler_btn = Gtk.Button(label="Open Labeler")
        labeler_btn.connect("clicked", self.on_open_labeler)
        btns.append(labeler_btn)
        del_btn = Gtk.Button(label="Delete Selected")
        del_btn.connect("clicked", self.on_delete_selected)
        btns.append(del_btn)
        self.append(btns)

        self.class_combo.connect("changed", lambda *_: self.load_images())
        self.reload_classes()

    def reload_classes(self):
        self.class_combo.remove_all()
        self.class_combo.append_text("")
        if self.classes_dir.exists():
            for d in sorted(self.classes_dir.iterdir()):
                if d.is_dir():
                    self.class_combo.append_text(d.name)
        if self.class_combo.get_model():
            iter_first = self.class_combo.get_model().get_iter_first()
            if iter_first:
                self.class_combo.set_active(0)

    def reload_classes_if_needed(self):
        self.reload_classes()
        self.load_images()

    def load_images(self):
        # Clear flow
        while True:
            c = self.flow.get_first_child()
            if c is None:
                break
            self.flow.remove(c)

        cls = self.class_combo.get_active_text()
        if not cls:
            return
        cls_dir = self.classes_dir / cls
        if not cls_dir.exists():
            return

        for img in sorted(cls_dir.glob("*.png")):
            btn = Gtk.Button()
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            try:
                image = Gtk.Image.new_from_file(str(img))
                image.set_pixel_size(96)
            except Exception:
                image = Gtk.Image.new_from_icon_name("image-x-generic")
            label = Gtk.Label(label=img.name)
            box.append(image)
            box.append(label)
            btn.set_child(box)
            # store file path
            btn.filepath = img
            self.flow.append(btn)

    def on_add_image(self, button):
        cls = self.class_combo.get_active_text()
        if not cls:
            dlg = Gtk.MessageDialog(transient_for=self.get_root(), modal=True,
                                    message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.OK,
                                    text="Please select a class first")
            dlg.connect("response", lambda d, r: d.destroy())
            dlg.present()
            return

        chooser = Gtk.FileChooserNative(title="Select image(s)", transient_for=self.get_root(), action=Gtk.FileChooserAction.OPEN)
        chooser.set_select_multiple(True)
        filter_imgs = Gtk.FileFilter()
        filter_imgs.add_mime_type("image/png")
        filter_imgs.add_mime_type("image/jpeg")
        filter_imgs.set_name("Images")
        chooser.add_filter(filter_imgs)
        chooser.connect("response", lambda dlg, resp: self._on_file_chosen(dlg, resp, cls))
        chooser.show()

    def _on_file_chosen(self, dialog, response, cls_name):
        if response != Gtk.ResponseType.OK:
            dialog.destroy()
            return
        files = dialog.get_files()
        dest = self.classes_dir / cls_name
        dest.mkdir(parents=True, exist_ok=True)
        for gfile in files:
            src = pathlib.Path(gfile.get_path())
            try:
                shutil.copy(src, dest / src.name)
            except Exception:
                pass
        dialog.destroy()
        self.load_images()

    def on_delete_selected(self, button):
        sel = self.flow.get_selected_child()
        if not sel:
            return
        fp = getattr(sel, "filepath", None)
        if not fp:
            return
        try:
            fp.unlink()
        except Exception:
            pass
        self.load_images()

    def on_open_labeler(self, button):
        """Launch the external template labeler script as a subprocess.

        Pass the selected class directory if present, otherwise pass the project classes dir.
        """
        cls = self.class_combo.get_active_text()
        if cls:
            target = self.classes_dir / cls
        else:
            target = self.classes_dir

        # locate the tools/templateGUI.py relative to repository root
        repo_root = Path(__file__).resolve().parents[1]
        script = repo_root / 'tools' / 'templateGUI.py'
        if not script.exists():
            dlg = Gtk.MessageDialog(transient_for=self.get_root(), modal=True,
                                    message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
                                    text=f"Labeler script not found: {script}")
            dlg.connect("response", lambda d, r: d.destroy())
            dlg.present()
            return

        try:
            subprocess.Popen([sys.executable, str(script), str(target)])
        except Exception as e:
            dlg = Gtk.MessageDialog(transient_for=self.get_root(), modal=True,
                                    message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
                                    text=f"Failed to launch labeler: {e}")
            dlg.connect("response", lambda d, r: d.destroy())
            dlg.present()
