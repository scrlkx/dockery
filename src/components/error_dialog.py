from typing import Any

from gi.repository import Adw

from ..utils.i18n import _


class ErrorDialog(Adw.MessageDialog):
    __gtype_name__ = "ErrorDialog"

    def __init__(self, message: str, **kwargs: Any):
        super().__init__(**kwargs)

        self.set_heading(_("Something went wrong!"))

        body = _("The operation could not be completed.")

        if message:
            body = f"{body}\n\n{message}"

        self.set_body(body)

        self.add_response("ok", _("Close"))
        self.set_default_response("ok")
        self.set_close_response("ok")
