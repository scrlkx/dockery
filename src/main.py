# main.py
#
# Copyright 2025 Daniel Freitas
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
from typing import Any, Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# pylint: disable=wrong-import-position
from gi.repository import Adw, Gio, GLib

from .window import DockeryWindow


class DockeryApplication(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.scrlkx.dockery",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
            resource_base_path="/com/scrlkx/dockery",
        )

        self.create_action("quit", lambda _, __: self.quit(), ["<control>q"])
        self.create_action("about", self.on_about_action)
        self.create_action("preferences", self.on_preferences_action)

    def do_activate(self) -> None:
        win = self.props.active_window

        if not win:
            win = DockeryWindow(application=self)

        win.present()

    def on_about_action(self, _: Gio.SimpleAction, __: GLib.Variant | None) -> None:
        about = Adw.AboutDialog(
            application_name="dockery",
            application_icon="com.scrlkx.dockery",
            developer_name="Daniel Freitas",
            version="0.1.0",
            developers=["Daniel Freitas"],
            copyright="© 2025 Daniel Freitas",
        )

        about.set_translator_credits("")
        about.present(self.props.active_window)

    def on_preferences_action(
        self, _: Gio.SimpleAction, __: GLib.Variant | None
    ) -> None:
        print("app.preferences action activated")

    def create_action(
        self,
        name: str,
        callback: Callable[[Gio.SimpleAction, Any], None],
        shortcuts: list[str] | None = None,
    ) -> None:
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)

        self.add_action(action)

        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(_):
    app = DockeryApplication()
    return app.run(sys.argv)
