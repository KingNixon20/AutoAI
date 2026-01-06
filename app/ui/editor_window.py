import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from app.ui.workflow_editor import WorkflowEditor
from app.ui.action_editor import ActionEditor
from app.ui.class_panel import ClassPanel
from app.ui.image_templates import ImageTemplates
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

        # Run button
        run_btn = Gtk.Button(label="Run Project")
        run_btn.connect("clicked", self.on_run)
        left_menu.append(run_btn)

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
        # Placeholder for running the workflow
        msg = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Run functionality not yet implemented"
        )
        msg.connect("response", lambda d, r: d.destroy())
        msg.present()

    def on_save(self, button):
        # Auto-save workflow using project name (overwrite if exists)
        from storage.project import Project
        from storage.workflow import Workflow

        name = self.project_path.name
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