import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, Graphene
import pathlib
from pathlib import Path
from PIL import Image
import cairo


class TemplateLabeler(Gtk.Box):
    """Simple GTK4 image browser + cropper for creating templates.

    - Open a folder of images (frames) to browse
    - Draw a rectangle to select a crop
    - Save the crop into a target class directory (passed at save time)
    """

    def __init__(self, project_path: pathlib.Path):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.project_path = Path(project_path)
        self.frames_dir = None

        self.files = []
        self.idx = 0
        self.img_orig = None
        self.pixbuf = None
        self.scale = 1.0
        self.image_offset = (0, 0)

        self.rect_start = None
        self.rect_end = None
        self.selection = None

        self.build_ui()

    def build_ui(self):
        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_open = Gtk.Button(label="Open Folder")
        btn_open.connect("clicked", lambda w: self.on_open())
        hb.append(btn_open)

        # Prev button as icon
        try:
            img_prev = Gtk.Image.new_from_icon_name("go-previous-symbolic")
            try:
                img_prev.set_pixel_size(18)
            except Exception:
                pass
            btn_prev = Gtk.Button()
            btn_prev.set_child(img_prev)
        except Exception:
            btn_prev = Gtk.Button(label="Prev")
        btn_prev.connect("clicked", lambda w: self.prev_image())
        hb.append(btn_prev)

        # Next button as icon
        try:
            img_next = Gtk.Image.new_from_icon_name("go-next-symbolic")
            try:
                img_next.set_pixel_size(18)
            except Exception:
                pass
            btn_next = Gtk.Button()
            btn_next.set_child(img_next)
        except Exception:
            btn_next = Gtk.Button(label="Next")
        btn_next.connect("clicked", lambda w: self.next_image())
        hb.append(btn_next)

        # Save Crop button as green image button placed next to Prev/Next
        save_icon_path = "/home/kingnixon/Documents/LinuxProjects/AutoAI/app/img/save.png"
        try:
            if Path(save_icon_path).exists():
                img_save = Gtk.Image.new_from_file(save_icon_path)
                try:
                    img_save.set_pixel_size(18)
                except Exception:
                    pass
                btn_save = Gtk.Button()
                btn_save.set_child(img_save)
            else:
                btn_save = Gtk.Button(label="Save")
        except Exception:
            btn_save = Gtk.Button(label="Save")
        btn_save.set_tooltip_text("Save Crop")
        try:
            btn_save.get_style_context().add_class('save-button')
        except Exception:
            pass
        btn_save.connect("clicked", lambda w: self._request_parent_save())
        hb.append(btn_save)

        # spacer so detach button sits on the right side of the header
        spacer = Gtk.Box()
        try:
            spacer.set_hexpand(True)
        except Exception:
            pass
        hb.append(spacer)

        # Detach button as an image button (fullscreen icon). Falls back to text if icon missing.
        icon_path = "/home/kingnixon/Documents/LinuxProjects/AutoAI/app/img/fullscreen.png"
        try:
            if Path(icon_path).exists():
                img = Gtk.Image.new_from_file(icon_path)
                try:
                    img.set_pixel_size(18)
                except Exception:
                    pass
                btn_detach = Gtk.Button()
                btn_detach.set_tooltip_text("Detach (fullscreen)")
                btn_detach.set_child(img)
            else:
                btn_detach = Gtk.Button(label="Detach")
        except Exception:
            btn_detach = Gtk.Button(label="Detach")

        btn_detach.connect("clicked", lambda w: self.on_detach())
        hb.append(btn_detach)

        # (Delete moved to Templates tab under thumbnails)

        # top "Save Crop" moved to ImageTemplates; embedded labeler no longer shows top save button

        self.append(hb)

        self.lbl_path = Gtk.Label(label="No folder loaded", halign=Gtk.Align.START)
        self.append(self.lbl_path)

        self.scroller = Gtk.ScrolledWindow()
        self.scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.scroller.set_vexpand(True)

        # Use an overlay: base image + transparent selection area on top
        self.image_widget = Gtk.Image()

        class SelectionArea(Gtk.DrawingArea):
            def __init__(self, parent):
                super().__init__()
                self.parent = parent

            def do_snapshot(self, snapshot):
                alloc = self.get_allocation()
                if alloc.width <= 0 or alloc.height <= 0:
                    return

                # get cairo context from snapshot for direct drawing
                # construct a Graphene.Rect for snapshot.append_cairo
                rect = Graphene.Rect()
                rect.init(0, 0, int(alloc.width), int(alloc.height))
                cr = snapshot.append_cairo(rect)

                # nothing to draw if no pixbuf
                if not getattr(self.parent, 'pixbuf', None):
                    return

                # draw the image
                Gdk.cairo_set_source_pixbuf(cr, self.parent.pixbuf, int(self.parent.image_offset[0]), int(self.parent.image_offset[1]))
                cr.paint()

                # draw selection rectangle if present
                if self.parent.rect_start and self.parent.rect_end:
                    cr.set_source_rgba(1, 0, 0, 0.7)
                    x0, y0 = self.parent.rect_start
                    x1, y1 = self.parent.rect_end
                    cr.set_line_width(2.0)
                    cr.rectangle(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
                    cr.stroke()

        self.sel_area = SelectionArea(self)
        # allow the selection area to expand so images fit the available space
        self.sel_area.set_vexpand(True)
        self.sel_area.set_hexpand(True)
        # GTK4: listen for allocation/property changes via notify::allocation
        self.sel_area.connect('notify::allocation', self._on_size_allocate)

        # gestures for drag selection on selection area
        drag = Gtk.GestureDrag.new()
        drag.connect("drag-begin", self._on_drag_begin)
        drag.connect("drag-update", self._on_drag_update)
        drag.connect("drag-end", self._on_drag_end)
        self.sel_area.add_controller(drag)

        self.overlay = Gtk.Overlay()
        self.overlay.set_vexpand(True)
        self.overlay.set_hexpand(True)
        self.overlay.set_child(self.image_widget)
        self.overlay.add_overlay(self.sel_area)

        self.scroller.set_child(self.overlay)
        self.append(self.scroller)

        self.status = Gtk.Label(label="")
        self.append(self.status)

    def on_open(self):
        dialog = Gtk.FileChooserDialog(title="Select Folder", transient_for=self.get_root(), action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons("_Cancel", Gtk.ResponseType.CANCEL, "_Open", Gtk.ResponseType.OK)

        def _resp(dlg, resp):
            if resp == Gtk.ResponseType.OK:
                try:
                    gfile = dlg.get_file()
                    folder = Path(gfile.get_path())
                    self.load_files(folder)
                    if self.files:
                        self.show_image()
                except Exception:
                    pass
            dlg.destroy()

        dialog.connect("response", _resp)
        dialog.present()

    def load_files(self, folder: Path):
        exts = ('*.png', '*.jpg', '*.jpeg', '*.bmp')
        items = []
        for e in exts:
            items += list(folder.glob(e))
        items = sorted(items)
        self.files = items
        self.frames_dir = folder
        self.lbl_path.set_text(f"{folder}  ({len(self.files)} frames)")

    def show_image(self):
        if not self.files:
            return
        p = self.files[self.idx]
        img = Image.open(p).convert('RGBA')
        self.img_orig = img
        self.current_path = p
        iw, ih = img.size

        alloc = self.sel_area.get_allocation()
        canvas_w, canvas_h = alloc.width, alloc.height
        if canvas_w < 10 or canvas_h < 10:
            screen = Gdk.Display.get_default().get_primary_monitor().get_geometry()
            canvas_w = screen.width
            canvas_h = int(screen.height * 0.9)

        scale = min(float(canvas_w) / float(iw), float(canvas_h) / float(ih))
        max_upscale = 3.0
        if scale > max_upscale:
            scale = max_upscale
        self.scale = float(scale)
        disp_w = max(1, int(iw * self.scale))
        disp_h = max(1, int(ih * self.scale))

        # store computed display size; actual pixbuf refresh happens in update_display()
        self._last_disp_size = (disp_w, disp_h)
        self._last_image_size = (iw, ih)
        # refresh display (and adjust to current sel_area size)
        self.update_display()

    def prev_image(self):
        if not self.files:
            return
        self.idx = max(0, self.idx - 1)
        self.show_image()

    def next_image(self):
        if not self.files:
            return
        self.idx = min(len(self.files) - 1, self.idx + 1)
        self.show_image()

    def on_snapshot(self, widget, snapshot):
        alloc = widget.get_allocation()
        if alloc.width <= 0 or alloc.height <= 0:
            return

        rect = Graphene.Rect()
        rect.init(0, 0, int(alloc.width), int(alloc.height))
        cr = snapshot.append_cairo(rect)

        # clear background
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(0, 0, alloc.width, alloc.height)
        cr.fill()

        if not self.pixbuf:
            return
        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, int(self.image_offset[0]), int(self.image_offset[1]))
        cr.paint()

        if self.rect_start and self.rect_end:
            cr.set_source_rgba(1, 0, 0, 0.7)
            x0, y0 = self.rect_start
            x1, y1 = self.rect_end
            cr.set_line_width(2.0)
            cr.rectangle(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
            cr.stroke()

    # Gesture handlers
    def _on_drag_begin(self, gesture, start_x, start_y):
        self.rect_start = (start_x, start_y)
        self.rect_end = None
        self.selection = None
        self.sel_area.queue_draw()

    def _on_drag_update(self, gesture, offset_x, offset_y):
        # compute current end point relative to start
        if not self.rect_start:
            return
        sx, sy = self.rect_start
        ex = sx + offset_x
        ey = sy + offset_y
        self.rect_end = (ex, ey)
        self.sel_area.queue_draw()

    def _on_drag_end(self, gesture, offset_x, offset_y):
        if not self.rect_start:
            return
        sx, sy = self.rect_start
        ex = sx + offset_x
        ey = sy + offset_y
        self.rect_end = (ex, ey)

        # translate to original image coords
        ox, oy = self.image_offset
        x0_rel = min(sx, ex) - ox
        y0_rel = min(sy, ey) - oy
        x1_rel = max(sx, ex) - ox
        y1_rel = max(sy, ey) - oy

        iw, ih = self.img_orig.size
        disp_w = int(iw * self.scale)
        disp_h = int(ih * self.scale)

        x0c = max(0, min(disp_w, x0_rel))
        x1c = max(0, min(disp_w, x1_rel))
        y0c = max(0, min(disp_h, y0_rel))
        y1c = max(0, min(disp_h, y1_rel))

        if abs(x1c - x0c) < 5 or abs(y1c - y0c) < 5:
            self.reset_rect()
            return

        ox0 = int(min(x0c, x1c) / self.scale)
        oy0 = int(min(y0c, y1c) / self.scale)
        ox1 = int(max(x0c, x1c) / self.scale)
        oy1 = int(max(y0c, y1c) / self.scale)
        self.selection = (ox0, oy0, ox1, oy1)
        self.sel_area.queue_draw()

    def reset_rect(self):
        self.rect_start = None
        self.rect_end = None
        self.selection = None
        self.sel_area.queue_draw()

    def update_display(self):
        """Recompute scaled pixbuf and offsets to fit `sel_area` allocation.

        Also remaps any existing selection from image coords to widget coords so
        crop accuracy is preserved after resizing.
        """
        if not getattr(self, 'img_orig', None) or not getattr(self, 'current_path', None):
            return
        iw, ih = self._last_image_size

        alloc = self.sel_area.get_allocation()
        canvas_w, canvas_h = alloc.width, alloc.height
        if canvas_w < 10 or canvas_h < 10:
            screen = Gdk.Display.get_default().get_primary_monitor().get_geometry()
            canvas_w = screen.width
            canvas_h = int(screen.height * 0.9)

        scale = min(float(canvas_w) / float(iw), float(canvas_h) / float(ih))
        max_upscale = 3.0
        if scale > max_upscale:
            scale = max_upscale
        self.scale = float(scale)
        disp_w = max(1, int(iw * self.scale))
        disp_h = max(1, int(ih * self.scale))

        # create/refresh pixbuf at display size
        p = self.current_path
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(p), disp_w, disp_h, True)
            self.pixbuf = pb
        except Exception:
            data = self.img_orig.resize((disp_w, disp_h), Image.LANCZOS)
            pb = GdkPixbuf.Pixbuf.new_from_data(data.tobytes(), GdkPixbuf.Colorspace.RGB, True, 8, disp_w, disp_h, disp_w*4)
            self.pixbuf = pb

        x = max(0, (alloc.width - disp_w) // 2)
        y = max(0, (alloc.height - disp_h) // 2)
        self.image_offset = (x, y)

        try:
            self.image_widget.set_from_pixbuf(self.pixbuf)
            self.image_widget.set_size_request(disp_w, disp_h)
        except Exception:
            pass

        # if we have an image-space selection, map it to widget-space for overlay
        if self.selection:
            ox0, oy0, ox1, oy1 = self.selection
            sx = int(ox0 * self.scale) + self.image_offset[0]
            sy = int(oy0 * self.scale) + self.image_offset[1]
            ex = int(ox1 * self.scale) + self.image_offset[0]
            ey = int(oy1 * self.scale) + self.image_offset[1]
            self.rect_start = (sx, sy)
            self.rect_end = (ex, ey)
        else:
            self.rect_start = None
            self.rect_end = None

        self.sel_area.queue_draw()

    def _on_size_allocate(self, widget, pspec):
        # called when sel_area allocation changes; recompute display
        self.update_display()

    def on_detach(self):
        if not getattr(self, 'img_orig', None):
            return

        # detach overlay into a new fullscreen window
        try:
            # remove overlay from scroller
            try:
                self.scroller.set_child(None)
            except Exception:
                pass

            win = Gtk.Window(transient_for=self.get_root())
            win.set_title("Detached Image View")

            # header with close button
            header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            close_btn = Gtk.Button(label="Close")
            header.append(close_btn)

            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            vbox.append(header)
            vbox.append(self.overlay)
            win.set_child(vbox)

            def _on_close(*_):
                try:
                    # reattach overlay back into scroller
                    vbox.remove(self.overlay)
                except Exception:
                    pass
                try:
                    self.scroller.set_child(self.overlay)
                except Exception:
                    pass
                try:
                    win.destroy()
                except Exception:
                    pass
                # recompute display in original container
                self.update_display()

            close_btn.connect('clicked', _on_close)
            win.present()
            win.fullscreen()
        except Exception:
            pass

    def _request_parent_delete(self):
        # Walk up the parent chain to find a handler `on_delete_selected`
        parent = self.get_parent()
        while parent is not None:
            if hasattr(parent, 'on_delete_selected'):
                try:
                    parent.on_delete_selected(None)
                except Exception:
                    pass
                return
            parent = parent.get_parent()

    def _request_parent_save(self):
        # Walk up the parent chain to find a handler `on_save_crop`
        parent = self.get_parent()
        while parent is not None:
            if hasattr(parent, 'on_save_crop'):
                try:
                    parent.on_save_crop()
                except Exception:
                    pass
                return
            parent = parent.get_parent()

    def on_save(self):
        if not self.selection:
            self.status.set_text('No selection: draw a rectangle first')
            return
        # caller should set target class dir before saving; we expose save_to_class
        self.status.set_text('Select a class in Templates tab and click Save Crop to save')

    def save_to_class(self, class_dir: Path):
        if not self.selection:
            raise RuntimeError('No selection')
        ensure_dir = Path(class_dir)
        ensure_dir.mkdir(parents=True, exist_ok=True)

        # crop from original image and save
        ox0, oy0, ox1, oy1 = self.selection
        crop = self.img_orig.crop((ox0, oy0, ox1, oy1))
        existing = list(ensure_dir.glob("*.png"))
        next_idx = len(existing) + 1
        class_name = ensure_dir.name
        safe_name = class_name.replace(' ', '_')
        outp = ensure_dir / f"{safe_name}_{next_idx:04d}.png"
        crop.save(outp)
        self.status.set_text(f"Saved {outp.name} to {ensure_dir}")
