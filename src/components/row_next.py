from gi.repository import Gtk


class RowNext(Gtk.Image):
    def __init__(self):
        super().__init__(icon_name="go-next-symbolic")

        self.set_margin_start(6)
        self.add_css_class("flat")
