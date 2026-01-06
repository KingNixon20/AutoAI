import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

import pathlib
import shutil
import subprocess
import sys
from pathlib import Path
from .template_labeler import TemplateLabeler


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
        # Template labeler widget will appear under the class selector
        self.append(selector)
        self.labeler = TemplateLabeler(self.project_path)
        # allow the labeler to take more vertical space so cropping area is larger
        try:
            self.labeler.set_vexpand(True)
        except Exception:
            pass
        self.append(self.labeler)

        # Flow of thumbnails
        self.flow = Gtk.FlowBox()
        self.flow.set_min_children_per_line(4)
        scroller = Gtk.ScrolledWindow()
        scroller.set_child(self.flow)
        # limit the thumbnail area height so the labeler gets priority; thumbnails will scroll
        try:
            scroller.set_vexpand(False)
            scroller.set_size_request(-1, 200)
        except Exception:
            pass
        self.append(scroller)

        # Delete button under thumbnails (red trashcan)
        btn_delete = Gtk.Button()
        try:
            img_trash = Gtk.Image.new_from_icon_name("user-trash-symbolic")
            try:
                img_trash.set_pixel_size(18)
            except Exception:
                pass
            btn_delete.set_child(img_trash)
        except Exception:
            btn_delete = Gtk.Button(label="Delete Selected")
        btn_delete.set_tooltip_text("Delete selected thumbnail")
        try:
            btn_delete.get_style_context().add_class('delete-button')
        except Exception:
            pass
        btn_delete.connect("clicked", lambda w: self.on_delete_selected(w))

        # Undo / Restore button (disabled until a delete occurs)
        btn_undo = Gtk.Button()
        try:
            img_undo = Gtk.Image.new_from_icon_name("edit-undo-symbolic")
            try:
                img_undo.set_pixel_size(18)
            except Exception:
                pass
            btn_undo.set_child(img_undo)
        except Exception:
            btn_undo = Gtk.Button(label="Restore")
        btn_undo.set_tooltip_text("Restore last deleted thumbnail")
        try:
            btn_undo.get_style_context().add_class('undo-button')
        except Exception:
            pass
        btn_undo.set_sensitive(False)
        btn_undo.connect("clicked", lambda w: self.on_undo_delete(w))

        # pack delete + undo under thumbnails
        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_row.append(btn_delete)
        btn_row.append(btn_undo)
        # keep references for state updates
        self._btn_delete = btn_delete
        self._btn_undo = btn_undo
        self.append(btn_row)

        # track currently selected thumbnail button
        self._selected_btn = None

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
        self._selected_btn = None

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
            # clicking a thumbnail selects it for deletion
            btn.connect("clicked", lambda b, bt=btn: self._on_thumb_clicked(bt))
            self.flow.append(btn)
        # update undo button sensitivity based on last deleted
        try:
            if getattr(self, '_last_deleted', None):
                self._btn_undo.set_sensitive(True)
            else:
                self._btn_undo.set_sensitive(False)
        except Exception:
            pass

    def _on_thumb_clicked(self, btn):
        # deselect previous
        if getattr(self, '_selected_btn', None):
            try:
                self._selected_btn.get_style_context().remove_class('selected')
            except Exception:
                pass
        # select new
        self._selected_btn = btn
        try:
            btn.get_style_context().add_class('selected')
        except Exception:
            pass
        # show filename in status for confirmation
        fp = getattr(btn, 'filepath', None)
        if fp:
            self.labeler.status.set_text(str(fp.name))

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

    def on_save_crop(self):
        """Save current crop from embedded labeler into selected class."""
        cls = self.class_combo.get_active_text()
        if not cls:
            dlg = Gtk.MessageDialog(transient_for=self.get_root(), modal=True,
                                    message_type=Gtk.MessageType.WARNING, buttons=Gtk.ButtonsType.OK,
                                    text="Please select a class first")
            dlg.connect("response", lambda d, r: d.destroy())
            dlg.present()
            return

        cls_dir = self.classes_dir / cls
        try:
            self.labeler.save_to_class(cls_dir)
            self.load_images()
        except Exception as e:
            dlg = Gtk.MessageDialog(transient_for=self.get_root(), modal=True,
                                    message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
                                    text=f"Failed to save crop: {e}")
            dlg.connect("response", lambda d, r: d.destroy())
            dlg.present()

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
        sel = getattr(self, '_selected_btn', None)
        if not sel:
            return
        fp = getattr(sel, 'filepath', None)
        if not fp:
            return
        # move to a per-class .recycle directory instead of permanent delete
        cls = self.class_combo.get_active_text()
        if not cls:
            return
        recycle_dir = self.classes_dir / cls / ".recycle"
        recycle_dir.mkdir(parents=True, exist_ok=True)
        dest = recycle_dir / fp.name
        try:
            shutil.move(str(fp), str(dest))
            # remember last deleted for undo
            self._last_deleted = (dest, self.classes_dir / cls)
            # enable undo
            try:
                self._btn_undo.set_sensitive(True)
            except Exception:
                pass
        except Exception:
            return
        # remove the widget from flow and clear selection
        try:
            self.flow.remove(sel)
        except Exception:
            pass
        self._selected_btn = None
        self.load_images()

    def on_undo_delete(self, button):
        last = getattr(self, '_last_deleted', None)
        if not last:
            return
        src, cls_dir = last
        orig = cls_dir / src.name
        try:
            shutil.move(str(src), str(orig))
            self._last_deleted = None
            try:
                self._btn_undo.set_sensitive(False)
            except Exception:
                pass
        except Exception:
            return
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

#
