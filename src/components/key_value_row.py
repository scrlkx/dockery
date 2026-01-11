from gi.repository import Adw, Gtk, Pango


class KeyValueRow(Adw.ActionRow):
    label: Gtk.Label

    def __init__(self, title: str, value: str):
        super().__init__()

        self.set_title(title)
        self.set_title_lines(1)

        self.label = Gtk.Label(label=value)
        self.label.set_margin_start(12)
        self.label.set_valign(Gtk.Align.CENTER)
        self.label.set_xalign(1.0)
        self.label.set_lines(1)
        self.label.set_ellipsize(Pango.EllipsizeMode.END)

        self.add_suffix(self.label)
