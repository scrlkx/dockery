from gi.repository import Gtk


class Badge(Gtk.Label):
    def __init__(
        self,
        text: str,
        style_class: str = "",
        margin_end: int = 0,
    ) -> None:
        super().__init__(label=text)

        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_end(margin_end)

        self.add_css_class("tag")
        self.add_css_class("caption")

        if style_class:
            self.add_css_class(style_class)
