from typing import Any

from gi.repository import Adw, Gio, GLib, GObject, Gtk

from ..utils.connection_profile import ConnectionProfile, get_profile_display_name
from ..utils.i18n import _


@Gtk.Template(resource_path="/com/scrlkx/dockery/dialogs/connection_dialog.ui")
class ConnectionDialog(Adw.Dialog):
    __gtype_name__ = "ConnectionDialog"

    __gsignals__ = {
        "connect-requested": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    cancel_button = Gtk.Template.Child()
    add_button = Gtk.Template.Child()
    name_entry = Gtk.Template.Child()
    type_combo = Gtk.Template.Child()
    uri_entry = Gtk.Template.Child()
    uri_list = Gtk.Template.Child()
    ssh_list = Gtk.Template.Child()
    jump_list = Gtk.Template.Child()
    ssh_host_entry = Gtk.Template.Child()
    ssh_port_spin = Gtk.Template.Child()
    ssh_user_entry = Gtk.Template.Child()
    ssh_identity_row = Gtk.Template.Child()
    ssh_identity_button = Gtk.Template.Child()
    ssh_identity_clear_button = Gtk.Template.Child()
    jump_host_entry = Gtk.Template.Child()
    jump_port_spin = Gtk.Template.Child()
    jump_user_entry = Gtk.Template.Child()
    jump_identity_row = Gtk.Template.Child()
    jump_identity_button = Gtk.Template.Child()
    jump_identity_clear_button = Gtk.Template.Child()

    KIND_MAP = {0: "unix", 1: "ssh"}
    KIND_INDEX = {"unix": 0, "ssh": 1}

    def __init__(
        self,
        profile: ConnectionProfile | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

        self._ssh_identity_path: str = ""
        self._jump_identity_path: str = ""

        if profile is not None:
            self.set_title(_("Edit connection"))
            self.add_button.set_label(_("Save"))

        self.register_events()
        self.build_ui()

        if profile is not None:
            self.load_profile(profile)

    def register_events(self) -> None:
        self.cancel_button.connect("clicked", self.on_cancel_clicked)
        self.add_button.connect("clicked", self.on_add_clicked)
        self.type_combo.connect("notify::selected", self.on_type_changed)
        self.uri_entry.connect("notify::text", self.on_input_changed)
        self.ssh_host_entry.connect("notify::text", self.on_input_changed)

        self.ssh_identity_button.connect("clicked", self._on_pick_identity, "ssh")
        self.ssh_identity_clear_button.connect(
            "clicked", self._on_clear_identity, "ssh"
        )
        self.jump_identity_button.connect("clicked", self._on_pick_identity, "jump")
        self.jump_identity_clear_button.connect(
            "clicked", self._on_clear_identity, "jump"
        )

    def build_ui(self) -> None:
        self.update_visibility()
        self.update_add_sensitivity()

    def load_profile(self, profile: ConnectionProfile) -> None:
        kind = profile.get("kind", "unix")
        self.type_combo.set_selected(self.KIND_INDEX.get(kind, 0))

        self.name_entry.set_text(profile.get("name", ""))

        if kind == "ssh":
            self.ssh_host_entry.set_text(profile.get("host", ""))
            self.ssh_port_spin.set_value(profile.get("port", 22))
            self.ssh_user_entry.set_text(profile.get("user", ""))

            identity = profile.get("identity_file", "")

            if identity:
                self._ssh_identity_path = identity
                self.ssh_identity_row.set_subtitle(identity)
                self.ssh_identity_clear_button.set_visible(True)

            self.jump_host_entry.set_text(profile.get("jump_host", ""))
            self.jump_port_spin.set_value(profile.get("jump_port", 22))
            self.jump_user_entry.set_text(profile.get("jump_user", ""))

            jump_identity = profile.get("jump_identity_file", "")

            if jump_identity:
                self._jump_identity_path = jump_identity
                self.jump_identity_row.set_subtitle(jump_identity)
                self.jump_identity_clear_button.set_visible(True)
        else:
            self.uri_entry.set_text(profile.get("uri", "unix:///var/run/docker.sock"))

        self.update_visibility()
        self.update_add_sensitivity()

    def on_type_changed(
        self,
        _combo: Adw.ComboRow,
        _pspec: GObject.ParamSpec,
    ) -> None:
        self.update_visibility()
        self.update_add_sensitivity()

    def on_input_changed(
        self,
        _entry: Adw.EntryRow,
        _pspec: GObject.ParamSpec,
    ) -> None:
        self.update_add_sensitivity()

    def update_visibility(self) -> None:
        kind = self.KIND_MAP.get(self.type_combo.get_selected(), "unix")
        is_ssh = kind == "ssh"

        self.uri_list.set_visible(not is_ssh)
        self.ssh_list.set_visible(is_ssh)
        self.jump_list.set_visible(is_ssh)

    def update_add_sensitivity(self) -> None:
        kind = self.KIND_MAP.get(self.type_combo.get_selected(), "unix")

        if kind == "ssh":
            has_input = bool(self.ssh_host_entry.get_text().strip())
        else:
            has_input = bool(self.uri_entry.get_text().strip())

        self.add_button.set_sensitive(has_input)

    def build_profile(self) -> ConnectionProfile:
        kind = self.KIND_MAP.get(self.type_combo.get_selected(), "unix")

        if kind == "ssh":
            profile = ConnectionProfile(
                kind="ssh",
                host=self.ssh_host_entry.get_text().strip(),
                port=int(self.ssh_port_spin.get_value()),
                user=self.ssh_user_entry.get_text().strip(),
            )

            if self._ssh_identity_path:
                profile["identity_file"] = self._ssh_identity_path

            jump_host = self.jump_host_entry.get_text().strip()

            if jump_host:
                profile["jump_host"] = jump_host
                profile["jump_port"] = int(self.jump_port_spin.get_value())

                jump_user = self.jump_user_entry.get_text().strip()

                if jump_user:
                    profile["jump_user"] = jump_user

                if self._jump_identity_path:
                    profile["jump_identity_file"] = self._jump_identity_path
        else:
            uri = self.uri_entry.get_text().strip()
            profile = ConnectionProfile(kind=kind, uri=uri)

        name = self.name_entry.get_text().strip()
        profile["name"] = name or get_profile_display_name(profile)

        return profile

    def _on_pick_identity(self, _button: Gtk.Button, target: str) -> None:
        dialog = Gtk.FileDialog(title=_("Select identity file"))

        ssh_filter = Gtk.FileFilter()
        ssh_filter.set_name(_("All files"))
        ssh_filter.add_pattern("*")

        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(ssh_filter)

        dialog.set_filters(filters)

        initial = Gio.File.new_for_path(GLib.get_home_dir() + "/.ssh")

        if initial.query_exists():
            dialog.set_initial_folder(initial)

        root = self.get_root()
        parent = root if isinstance(root, Gtk.Window) else None
        dialog.open(parent, None, self._on_file_chosen, target)

    def _on_file_chosen(
        self,
        dialog: Gtk.FileDialog,
        result: Gio.AsyncResult,
        target: str,
    ) -> None:
        try:
            file = dialog.open_finish(result)
        except GLib.Error:
            return

        path = file.get_path()

        if path is None:
            return

        if target == "ssh":
            self._ssh_identity_path = path
            self.ssh_identity_row.set_subtitle(path)
            self.ssh_identity_clear_button.set_visible(True)
        else:
            self._jump_identity_path = path
            self.jump_identity_row.set_subtitle(path)
            self.jump_identity_clear_button.set_visible(True)

    def _on_clear_identity(self, _button: Gtk.Button, target: str) -> None:
        if target == "ssh":
            self._ssh_identity_path = ""
            self.ssh_identity_row.set_subtitle("")
            self.ssh_identity_clear_button.set_visible(False)
        else:
            self._jump_identity_path = ""
            self.jump_identity_row.set_subtitle("")
            self.jump_identity_clear_button.set_visible(False)

    def on_add_clicked(self, _: Gtk.Button) -> None:
        profile = self.build_profile()

        self.emit("connect-requested", profile)
        self.force_close()

    def on_cancel_clicked(self, _: Gtk.Button) -> None:
        self.force_close()
