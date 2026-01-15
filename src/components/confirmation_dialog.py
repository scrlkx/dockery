from typing import Any

from gi.repository import Adw, GObject

from ..utils.i18n import _


class ConfirmationDialog(Adw.MessageDialog):
    __gtype_name__ = "ConfirmationDialog"

    title = GObject.Property(type=str, default=_("Are you sure?"))
    body = GObject.Property(type=str, default=_("Do you really want to continue?"))
    action_label = GObject.Property(type=str, default=_("Continue"))

    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        self.set_heading(self.title)
        self.set_body(self.body)

        self.add_response("cancel", _("Cancel"))
        self.add_response("continue", self.action_label)

        self.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        self.set_default_response("cancel")
        self.set_close_response("cancel")
