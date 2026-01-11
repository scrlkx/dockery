import gettext


def _(message: str) -> str:
    return gettext.gettext(message)
