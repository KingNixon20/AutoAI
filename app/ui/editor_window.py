import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

from app.ui.workflow_editor import WorkflowEditor
from app.ui.action_editor import ActionEditor
from app.ui.class_panel import ClassPanel
from app.ui.image_templates import ImageTemplates
from app.ui.run_options import RunOptions
import pathlib


class EditorWindow(Gtk.ApplicationWindow):
    def __init__(self, application, project_path):
        super().__init__(application=application, title=f"Editor – {pathlib.Path(project_path).name}")
        self.set_default_size(1400, 800)
        self.project_path = pathlib.Path(project_path)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(vbox)

        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label=f"Project: {self.project_path.name}"))
        self.set_titlebar(header)

        # Main layout with resizable panels using Gtk.Paned
        # Outer paned: left panel | (center + right)
        outer_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.append(outer_paned)

        # === LEFT SIDEBAR ===
        left_menu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        left_menu.set_size_request(200, -1)  # Minimum width
        left_menu.set_margin_start(12)
        left_menu.set_margin_end(12)
        left_menu.set_margin_top(12)
        left_menu.set_margin_bottom(12)
        
        left_title = Gtk.Label(label="Project Settings")
        left_title.get_style_context().add_class("title-4")
        left_menu.append(left_title)
        
        # Project name
        name_label = Gtk.Label(label="Project Name:")
        name_label.set_halign(Gtk.Align.START)
        left_menu.append(name_label)
        
        self.name_entry = Gtk.Entry()
        self.name_entry.set_text(self.project_path.name)
        left_menu.append(self.name_entry)

        # Spacer
        spacer1 = Gtk.Box()
        spacer1.set_vexpand(True)
        left_menu.append(spacer1)

        # Save button
        save_btn = Gtk.Button(label="Save Workflow")
        save_btn.get_style_context().add_class("suggested-action")
        save_btn.connect("clicked", self.on_save)
        left_menu.append(save_btn)

        # Dry-run toggle
        self.dry_run_check = Gtk.CheckButton(label="Dry-run (no input actions)")
        self.dry_run_check.set_active(True)
        left_menu.append(self.dry_run_check)

        # Run button
        run_btn = Gtk.Button(label="Run Project")
        run_btn.connect("clicked", self.on_run)
        left_menu.append(run_btn)

        # Screenshot recorder launcher
        shot_btn = Gtk.Button(label="Screenshot Recorder")
        shot_btn.connect("clicked", lambda b: self._open_screenshot_recorder())
        left_menu.append(shot_btn)

        # wrap left menu in a titled frame for a cleaner look
        left_frame = Gtk.Frame()
        left_frame.set_label("Project Settings")
        left_frame.set_child(left_menu)
        outer_paned.set_start_child(left_frame)
        outer_paned.set_resize_start_child(False)
        outer_paned.set_shrink_start_child(False)

        # Inner paned: center | right panel
        inner_paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        outer_paned.set_end_child(inner_paned)
        outer_paned.set_resize_end_child(True)
        outer_paned.set_shrink_end_child(False)

        # === CENTER CONTENT AREA (TABBED) ===
        center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        center.set_size_request(400, -1)  # Minimum width
        center.set_margin_start(12)
        center.set_margin_end(12)
        center.set_margin_top(12)
        center.set_margin_bottom(12)

        # Create notebook for tabs
        self.notebook = Gtk.Notebook()
        self.notebook.set_vexpand(True)
        self.notebook.set_hexpand(True)

        # === TAB 1: WORKFLOW ACTIONS ===
        workflow_tab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        # Action dropdown bar (compact grid)
        action_bar = Gtk.Grid(column_spacing=12, row_spacing=6)
        action_label = Gtk.Label(label="Action Type:")
        action_label.set_halign(Gtk.Align.START)
        action_bar.attach(action_label, 0, 0, 1, 1)

        self.action_combo = Gtk.ComboBoxText()
        for action in ["Delay", "FindAndClick", "TypeText", "KeyPress"]:
            self.action_combo.append_text(action)
        self.action_combo.set_active(0)
        action_bar.attach(self.action_combo, 1, 0, 1, 1)

        insert_btn = Gtk.Button(label="Insert Action")
        insert_btn.connect("clicked", self.on_insert_action)
        action_bar.attach(insert_btn, 2, 0, 1, 1)

        workflow_tab.append(action_bar)

        # Workflow editor wrapped in a frame for visual grouping
        self.editor = WorkflowEditor()
        self.editor.set_hexpand(True)
        self.editor.set_vexpand(True)
        wf_frame = Gtk.Frame()
        wf_frame.set_label("Workflow")
        wf_frame.set_child(self.editor)
        workflow_tab.append(wf_frame)

        # Add workflow tab
        workflow_label = Gtk.Label(label="Actions")
        self.notebook.append_page(workflow_tab, workflow_label)

        # === TAB 2: CLASS EDITOR ===
        # Ensure action editor exists so class panel callbacks can reference it
        self.action_editor = ActionEditor(self.project_path)

        # Create image templates widget so class changes can refresh both
        self.image_templates = ImageTemplates(self.project_path)

        self.class_panel = ClassPanel(
            self.project_path,
            on_classes_changed=lambda: (self.action_editor.reload_classes_if_needed(), self.image_templates.reload_classes_if_needed())
        )
        self.class_panel.set_hexpand(True)
        self.class_panel.set_vexpand(True)
        
        class_label = Gtk.Label(label="Classes")
        self.notebook.append_page(self.class_panel, class_label)

        # === TAB 3: IMAGE TEMPLATES ===
        templates_label = Gtk.Label(label="Templates")
        self.notebook.append_page(self.image_templates, templates_label)

        center.append(self.notebook)
        inner_paned.set_start_child(center)
        inner_paned.set_resize_start_child(True)
        inner_paned.set_shrink_start_child(False)

        # === RIGHT SIDEBAR (Action Settings) ===
        right_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        right_panel.set_size_request(250, -1)  # Minimum width
        right_panel.set_margin_start(12)
        right_panel.set_margin_end(12)
        right_panel.set_margin_top(12)
        right_panel.set_margin_bottom(12)

        # Action editor inside a titled frame
        action_frame = Gtk.Frame()
        action_frame.set_label("Action Settings")
        action_frame.set_child(self.action_editor)
        right_panel.append(action_frame)

        # Run options placed under the action editor in the right sidebar
        self.run_options = RunOptions()
        right_panel.append(self.run_options)

        inner_paned.set_end_child(right_panel)
        inner_paned.set_resize_end_child(False)
        inner_paned.set_shrink_end_child(False)

        # Set initial paned positions
        outer_paned.set_position(280)
        inner_paned.set_position(700)

        # Keep action settings in sync with combo selection
        self.action_combo.connect("changed", self._on_action_changed)
        # Initialize with first action
        self.action_editor.set_action_type(self.action_combo.get_active_text())

        # Connect to notebook page changes to update right panel
        self.notebook.connect("switch-page", self._on_tab_changed)

        # After UI setup, try loading the most recent workflow for this project
        self._load_existing_workflow()

    def _on_tab_changed(self, notebook, page, page_num):
        """Update right panel based on active tab."""
        # When switching back to Actions tab, reload classes in case they were added
        if page_num == 0:  # Actions tab
            self.action_editor.reload_classes_if_needed()

    def _on_action_changed(self, combo):
        action_type = combo.get_active_text()
        if action_type:
            self.action_editor.set_action_type(action_type)

    def on_insert_action(self, button):
        typ = self.action_combo.get_active_text()
        if not typ:
            return
        
        # Get parameters from action editor
        self.action_editor.set_action_type(typ)
        params = self.action_editor.get_params()
        
        # Create step and add to workflow
        step = {"type": typ, "params": params}
        self.editor.add_step(step)

    def on_run(self, button):
        # Run the current workflow using the WorkflowExecutor (with dry-run option)
        from engine.executor import WorkflowExecutor
        from storage.workflow import Workflow

        steps = self.editor.get_steps()
        if not steps:
            dlg = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text="No steps to run"
            )
            dlg.connect("response", lambda d, r: d.destroy())
            dlg.present()
            return

        wf = Workflow(name=self.name_entry.get_text().strip() or self.project_path.name, steps=steps)
        executor = WorkflowExecutor()
        # gather run options from the run options widget and pass to executor
        run_options = {}
        try:
            run_options = self.run_options.get_settings()
        except Exception:
            run_options = {}
        dry = bool(self.dry_run_check.get_active())

        # Create a dialog to show progress and allow stopping
        dlg = Gtk.Dialog(title="Running Workflow", transient_for=self, modal=True)
        dlg.add_buttons("_Close", Gtk.ResponseType.CLOSE)
        content = dlg.get_content_area()
        status_label = Gtk.Label(label="Starting...")
        status_label.set_wrap(True)
        status_label.set_max_width_chars(60)
        content.append(status_label)

        # Iteration indicator
        iteration_label = Gtk.Label(label="Iteration: -")
        iteration_label.set_halign(Gtk.Align.START)
        content.append(iteration_label)

        stop_btn = Gtk.Button(label="Stop")
        stop_btn.connect("clicked", lambda b: executor.stop())
        content.append(stop_btn)

        dlg.present()

        def on_update(msg: str):
            # Update status label
            GLib.idle_add(status_label.set_text, str(msg))
            # If executor sends iteration messages like 'Starting iteration N', update iteration label
            try:
                if isinstance(msg, str) and msg.startswith('Starting iteration'):
                    parts = msg.split()
                    if len(parts) >= 3:
                        num = parts[2].strip()
                        GLib.idle_add(iteration_label.set_text, f"Iteration: {num}")
                elif isinstance(msg, str) and msg.startswith('Completed iteration'):
                    parts = msg.split()
                    if len(parts) >= 3:
                        num = parts[2].strip()
                        GLib.idle_add(iteration_label.set_text, f"Completed: {num}")
            except Exception:
                pass

        def on_finished(success: bool, message: str):
            def _finish():
                status_label.set_text(f"Finished: {message}")
                return False
            GLib.idle_add(_finish)

        executor.run(wf, dry_run=dry, options=run_options, on_update=on_update, on_finished=on_finished)

    def on_save(self, button):
        # Auto-save workflow using project name (overwrite if exists)
        from storage.project import Project
        from storage.workflow import Workflow
        # prefer the name in the Project Name entry so users can rename workflows
        name = self.name_entry.get_text().strip() or self.project_path.name
        proj = Project(self.project_path)
        steps = self.editor.get_steps()
        wf = Workflow(name=name, steps=steps)
        path = proj.save_workflow(wf)

        # Show confirmation
        msg = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=f"Saved workflow to {path}"
        )
        msg.connect("response", lambda d, r: d.destroy())
        msg.present()

    def _on_save_response(self, dialog, response_id, entry):
        from storage.project import Project
        from storage.workflow import Workflow
        
        name = entry.get_text().strip()
        dialog.destroy()

        if response_id == Gtk.ResponseType.OK and name:
            project_dir = self.project_path
            proj = Project(project_dir)
            steps = self.editor.get_steps()
            wf = Workflow(name=name, steps=steps)
            path = proj.save_workflow(wf)
            
            # Show confirmation
            msg = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.INFO,
                buttons=Gtk.ButtonsType.OK,
                text=f"Saved workflow to {path}"
            )
            msg.connect("response", lambda d, r: d.destroy())
            msg.present()

    def _load_existing_workflow(self):
        """Load the most recently saved workflow for this project (if any)."""
        from storage.project import Project

        proj = Project(self.project_path)
        workflows = proj.list_workflows()
        if not workflows:
            return

        # workflows is a list of (path, Workflow) tuples. Pick the most-recent file.
        try:
            workflows_sorted = sorted(workflows, key=lambda t: t[0].stat().st_mtime, reverse=True)
        except Exception:
            workflows_sorted = workflows

        path, wf = workflows_sorted[0]

        # populate UI
        try:
            self.name_entry.set_text(wf.name)
        except Exception:
            pass

        try:
            self.editor.clear_steps()
            for step in wf.steps:
                self.editor.add_step(step)
        except Exception:
            pass

    def _open_screenshot_recorder(self):
        try:
            from app.ui.screenshot_recorder import ScreenshotRecorder
            win = ScreenshotRecorder(self.project_path, transient_for=self)
            win.present()
        except Exception as e:
            dlg = Gtk.MessageDialog(transient_for=self, modal=True,
                                    message_type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK,
                                    text=f"Failed to open screenshot recorder: {e}")
            dlg.connect("response", lambda d, r: d.destroy())
            dlg.present()
#
