from typing import Any

from gi.repository import Adw

from ..utils.i18n import _


class ConnectionErrorDialog(Adw.MessageDialog):
    __gtype_name__ = "ConnectionErrorDialog"

    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        body = _("Could not load Docker data.")

        if message:
            body = f"{body}\n\n{message}"

        self.set_heading(_("Connection lost"))
        self.set_body(body)

        self.add_response("reconnect", _("Reconnect"))
        self.add_response("disconnect", _("Disconnect"))
        self.set_response_appearance("disconnect", Adw.ResponseAppearance.DESTRUCTIVE)
        self.set_default_response("reconnect")
        self.set_close_response("reconnect")
