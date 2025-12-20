import docker
from gi.repository import Adw, Gtk


@Gtk.Template(resource_path="/com/scrlkx/dockery/container_page.ui")
class ContainerPage(Adw.NavigationPage):
    __gtype_name__ = "ContainerPage"

    name_label = Gtk.Template.Child()
    quick_actions_box = Gtk.Template.Child()

    def __init__(self, container):
        super().__init__()

        self.container_name = container.name

        self._load_container()
        self._load_quick_actions()

    def _load_container(self):
        client = docker.from_env()

        self.container = client.containers.get(self.container_name)

        self.set_title(self.container.name)
        self.name_label.set_text(self.container.name)

    def _load_quick_actions(self):
        actions_map = {
            "running": [
                ("Pause", "pause.svg", self.on_pause_clicked),
                ("Stop", "circle-crossed.svg", self.on_stop_clicked),
                ("Restart", "reload.svg", self.on_restart_clicked),
                ("Kill", "cross.svg", self.on_kill_clicked),
            ],
            "restarting": [
                ("Stop", "circle-crossed.svg", self.on_stop_clicked),
                ("Kill", "cross.svg", self.on_kill_clicked),
            ],
            "paused": [
                ("Resume", "play.svg", self.on_resume_clicked),
                ("Stop", "circle-crossed.svg", self.on_stop_clicked),
            ],
            "stopped": [
                ("Start", "play.svg", self.on_start_clicked),
                ("Remove", "trash.svg", self.on_remove_clicked),
            ],
            "exited": [
                ("Start", "play.svg", self.on_start_clicked),
                ("Remove", "trash.svg", self.on_remove_clicked),
            ],
            "created": [
                ("Start", "start.svg", self.on_start_clicked),
                ("Remove", "trash.svg", self.on_remove_clicked),
            ],
        }

        actions = actions_map.get(self.container.status, [])

        for label, icon, callback in actions:
            button = self._create_quick_action_button(label, icon, callback)
            self.quick_actions_box.append(button)

    def _create_quick_action_button(self, label_text, icon_name, callback):
        box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=6,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
        )

        image = Gtk.Image.new_from_resource(f"/com/scrlkx/dockery/icons/{icon_name}")
        box.append(image)

        label = Gtk.Label(label=label_text)
        box.append(label)

        button = Gtk.Button(hexpand=True)
        button.set_child(box)
        button.connect("clicked", callback)

        return button

    def on_start_clicked(self, _):
        self.container.start()

        self._load_container()
        self._load_quick_actions()

    def on_pause_clicked(self, _):
        self.container.pause()

        self._load_container()
        self._load_quick_actions()

    def on_resume_clicked(self, _):
        self.container.resume()

        self._load_container()
        self._load_quick_actions()

    def on_stop_clicked(self, _):
        self.container.stop()

        self._load_container()
        self._load_quick_actions()

    def on_restart_clicked(self, _):
        self.container.restart()

        self._load_container()
        self._load_quick_actions()

    def on_kill_clicked(self, _):
        self.container.kill()

        self._load_container()
        self._load_quick_actions()

    def on_remove_clicked(self, _):
        self.container.remove()

        self._load_container()
        self._load_quick_actions()
