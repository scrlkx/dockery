from gi.repository import Adw, Gtk


class KeyValueRow(Adw.ActionRow):
    label: Gtk.Label

    def __init__(self, title: str, value: str):
        super().__init__()

        self.set_title(title)

        self.label = Gtk.Label(label=value)
        self.label.set_valign(Gtk.Align.CENTER)
        self.label.set_xalign(1.0)

        self.add_suffix(self.label)
