import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from app.ui.projects_view import ProjectsView
from app.ui.settings_view import SettingsView


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__(application=application, title="AutoAI")
        self.set_default_size(1000, 700)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.set_child(hbox)

        # Stack + Sidebar on the left
        self.stack = Gtk.Stack()
        sidebar = Gtk.StackSidebar()
        sidebar.set_stack(self.stack)

        side_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        side_container.append(sidebar)
        # Make sidebar span full height and request a larger width
        side_container.set_vexpand(True)
        side_container.set_size_request(240, -1)
        sidebar.set_vexpand(True)
        hbox.append(side_container)

        # Add content pages
        projects_view = ProjectsView(application)
        settings_view = SettingsView()

        self.stack.add_titled(projects_view, "projects", "Projects")
        self.stack.add_titled(settings_view, "settings", "Settings")

        # Ensure main stack expands to fill remaining space
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        hbox.append(self.stack)

#
