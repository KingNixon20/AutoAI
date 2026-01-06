#!/usr/bin/env python3
"""
GTK-based Template Labeler for the EVEBOT project.

Features:
- Browse images in the `detections/` folder (default) or choose another folder.
- Draw a rectangle to crop a template and save to `templates/` as `<class>__<id>.png`.
- Mark a crop/frame as positive or negative; writes JSONL feedback entries.

This replaces an older Tkinter tool and integrates more cleanly with the
EVEBOT repository layout.
"""
from pathlib import Path
import json
import time
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf
from PIL import Image


# --- Helpers and paths ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATES_DIR = PROJECT_ROOT / 'templates'
DEFAULT_DETECTIONS_DIR = PROJECT_ROOT / 'detections'
DEFAULT_DATA_LABELS = PROJECT_ROOT / 'data' / 'labels.jsonl'


def ensure_templates_dir():
    DEFAULT_TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


def next_template_id_for(class_name):
    ensure_templates_dir()
    existing = list(DEFAULT_TEMPLATES_DIR.glob(f"{class_name}__*.png"))
    ids = []
    for p in existing:
        stem = p.stem
        if "__" in stem:
            try:
                ids.append(int(stem.split("__")[-1]))
            except Exception:
                pass
    return max(ids) + 1 if ids else 1


def save_feedback_entry(out_path: Path, frame_relpath, bbox, label, positive):
    entry = {
        'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'frame': str(frame_relpath),
        'bbox': bbox,
        'label': label,
        'positive': bool(positive),
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')


# --- GTK App ---
class TemplateLabeler(Gtk.Window):
    def __init__(self, frames_dir=None):
        super().__init__(title='Template Labeler')
        self.set_default_size(1000, 700)
        self.set_border_width(6)

        self.frames_dir = Path(frames_dir) if frames_dir else (DEFAULT_DETECTIONS_DIR if DEFAULT_DETECTIONS_DIR.exists() else None)
        if self.frames_dir and not self.frames_dir.exists():
            self.frames_dir = None

        self.files = []
        self.idx = 0
        self.img_orig = None  # PIL image
        self.pixbuf = None
        self.scale = 1.0
        self.image_offset = (0, 0)

        self.rect_start = None
        self.rect_end = None
        self.selection = None  # (x1,y1,x2,y2) in original image coords

        self.feedback_out = (self.frames_dir / 'feedback.jsonl') if self.frames_dir else DEFAULT_DATA_LABELS
        self.labels_out = DEFAULT_DATA_LABELS

        self.build_ui()
        self.connect('key-press-event', self.on_key)

        if self.frames_dir:
            self.load_files(self.frames_dir)
            if self.files:
                self.show_image()

    def build_ui(self):
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = 'Template Labeler'
        self.set_titlebar(hb)

        btn_open = Gtk.Button.new_with_label('Open Folder')
        btn_open.connect('clicked', self.on_open)
        hb.pack_start(btn_open)

        btn_prev = Gtk.Button.new_with_label('Prev')
        btn_prev.connect('clicked', lambda w: self.prev_image())
        hb.pack_start(btn_prev)

        btn_next = Gtk.Button.new_with_label('Next')
        btn_next.connect('clicked', lambda w: self.next_image())
        hb.pack_start(btn_next)

        btn_save = Gtk.Button.new_with_label('Save Template')
        btn_save.connect('clicked', lambda w: self.save_template())
        hb.pack_end(btn_save)

        btn_pos = Gtk.Button.new_with_label('Mark +')
        btn_pos.connect('clicked', lambda w: self.mark_label(True))
        hb.pack_end(btn_pos)

        btn_neg = Gtk.Button.new_with_label('Mark -')
        btn_neg.connect('clicked', lambda w: self.mark_label(False))
        hb.pack_end(btn_neg)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        self.lbl_path = Gtk.Label(label='No folder loaded', xalign=0)
        vbox.pack_start(self.lbl_path, False, False, 0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        vbox.pack_start(scrolled, True, True, 0)

        self.darea = Gtk.DrawingArea()
        self.darea.set_size_request(800, 600)
        self.darea.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.BUTTON_MOTION_MASK)
        self.darea.connect('draw', self.on_draw)
        self.darea.connect('button-press-event', self.on_mouse_down)
        self.darea.connect('motion-notify-event', self.on_mouse_move)
        self.darea.connect('button-release-event', self.on_mouse_up)
        scrolled.add(self.darea)

        self.status = Gtk.Label(label='')
        vbox.pack_start(self.status, False, False, 0)

    def on_open(self, _w=None):
        dialog = Gtk.FileChooserDialog(title='Select Folder', parent=self, action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, 'Open', Gtk.ResponseType.OK)
        if self.frames_dir:
            dialog.set_current_folder(str(self.frames_dir))
        resp = dialog.run()
        if resp == Gtk.ResponseType.OK:
            folder = Path(dialog.get_filename())
            self.frames_dir = folder
            self.feedback_out = self.frames_dir / 'feedback.jsonl'
            self.load_files(self.frames_dir)
            self.idx = 0
            if self.files:
                self.show_image()
        dialog.destroy()

    def load_files(self, folder: Path):
        exts = ('*.png', '*.jpg', '*.jpeg', '*.bmp')
        items = []
        for e in exts:
            items += list(folder.glob(e))
        items = sorted(items)
        self.files = items
        self.lbl_path.set_text(f"{folder}  ({len(self.files)} frames)")
        if not self.files:
            self.show_message(f'No image files found in {folder}')

    def show_message(self, text):
        self.status.set_text(text)

    def show_image(self):
        if not self.files:
            return
        p = self.files[self.idx]
        # load PIL image for cropping
        img = Image.open(p).convert('RGBA')
        self.img_orig = img
        iw, ih = img.size

        alloc = self.darea.get_allocation()
        canvas_w, canvas_h = alloc.width, alloc.height
        if canvas_w < 10 or canvas_h < 10:
            # fallback to screen size
            screen = Gdk.Screen.get_default()
            canvas_w = screen.get_width()
            canvas_h = int(screen.get_height() * 0.9)

        scale = min(float(canvas_w) / float(iw), float(canvas_h) / float(ih))
        max_upscale = 3.0
        if scale > max_upscale:
            scale = max_upscale
        self.scale = float(scale)
        disp_w = max(1, int(iw * self.scale))
        disp_h = max(1, int(ih * self.scale))

        # create pixbuf from file scaled
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(p), disp_w, disp_h, True)
            self.pixbuf = pb
        except Exception:
            # fallback: convert via PIL
            data = img.resize((disp_w, disp_h), Image.LANCZOS)
            pb = GdkPixbuf.Pixbuf.new_from_data(data.tobytes(), GdkPixbuf.Colorspace.RGB, True, 8, disp_w, disp_h, disp_w*4)
            self.pixbuf = pb

        # center image
        alloc = self.darea.get_allocation()
        x = max(0, (alloc.width - disp_w) // 2)
        y = max(0, (alloc.height - disp_h) // 2)
        self.image_offset = (x, y)
        self.queue_draw()
        self.show_message(f'{p.name} ({self.idx+1}/{len(self.files)})')

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

    def on_draw(self, widget, cr):
        # draw background
        alloc = widget.get_allocation()
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(0, 0, alloc.width, alloc.height)
        cr.fill()

        if not self.pixbuf:
            return False
        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, self.image_offset[0], self.image_offset[1])
        cr.paint()

        # draw selection rectangle if present
        if self.rect_start and self.rect_end:
            cr.set_source_rgba(1, 0, 0, 0.7)
            x0, y0 = self.rect_start
            x1, y1 = self.rect_end
            cr.set_line_width(2.0)
            cr.rectangle(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
            cr.stroke()

        return False

    def on_mouse_down(self, widget, event):
        if event.button != 1:
            return
        self.rect_start = (event.x, event.y)
        self.rect_end = None
        self.selection = None
        self.queue_draw()

    def on_mouse_move(self, widget, event):
        if not self.rect_start:
            return
        self.rect_end = (event.x, event.y)
        self.queue_draw()

    def on_mouse_up(self, widget, event):
        if event.button != 1 or not self.rect_start:
            return
        x0_canvas, y0_canvas = self.rect_start
        x1_canvas, y1_canvas = (event.x, event.y)
        ox, oy = self.image_offset
        x0_rel = x0_canvas - ox
        y0_rel = y0_canvas - oy
        x1_rel = x1_canvas - ox
        y1_rel = y1_canvas - oy

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
        # store rect in canvas coords for drawing
        self.rect_end = (x1_canvas, y1_canvas)
        self.queue_draw()

    def reset_rect(self):
        self.rect_start = None
        self.rect_end = None
        self.selection = None
        self.queue_draw()

    def ask_class_dialog(self):
        dialog = Gtk.Dialog('Class name', self, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
        dialog.set_default_size(200, 80)
        box = dialog.get_content_area()
        entry = Gtk.Entry()
        entry.set_text('')
        box.add(entry)
        entry.show()
        resp = dialog.run()
        name = entry.get_text().strip()
        dialog.destroy()
        if resp == Gtk.ResponseType.OK and name:
            return name
        return None

    def save_template(self):
        if not self.selection:
            self.show_message('No selection: draw a rectangle first')
            return
        cls = self.ask_class_dialog()
        if not cls:
            return
        ensure_templates_dir()
        tid = next_template_id_for(cls)
        out = DEFAULT_TEMPLATES_DIR / f"{cls}__{tid}.png"
        crop = self.img_orig.crop(self.selection)
        crop.save(str(out))
        self.show_message(f'Template saved: {out.name}')
        frame_rel = self.files[self.idx].relative_to(PROJECT_ROOT)
        save_feedback_entry(self.feedback_out, frame_rel, list(self.selection), cls, True)

    def mark_label(self, positive: bool):
        cls = self.ask_class_dialog()
        if not cls:
            return
        bbox = None
        if self.selection:
            bbox = list(self.selection)
        frame_rel = self.files[self.idx].relative_to(PROJECT_ROOT)
        save_feedback_entry(self.feedback_out, frame_rel, bbox, cls, positive)
        save_feedback_entry(self.labels_out, frame_rel, bbox, cls, positive)
        self.show_message(f"Saved {'positive' if positive else 'negative'} label for {cls}")
        self.next_image()

    def on_key(self, _w, event):
        key = Gdk.keyval_name(event.keyval)
        if key == 'Left':
            self.prev_image()
        elif key == 'Right':
            self.next_image()
        elif key in ('s', 'S'):
            self.save_template()
        elif key in ('p', 'P'):
            self.mark_label(True)
        elif key in ('n', 'N'):
            self.mark_label(False)
        elif key in ('r', 'R'):
            self.reset_rect()


def main():
    app = TemplateLabeler()
    app.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()