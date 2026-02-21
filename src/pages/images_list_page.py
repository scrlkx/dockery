from typing import Any

from docker.models.images import Image
from gi.repository import Adw, GObject, Gtk

from ..components.async_list import AsyncList
from ..components.badge import Badge
from ..components.row_next import RowNext
from ..utils.docker import (
    get_image_last_tag,
    get_image_size,
    get_images,
)
from ..utils.i18n import _
from ..utils.ui import humanize_size


class ImageRow(Adw.ActionRow):
    __gtype_name__ = "ImageRow"

    short_id = GObject.Property(type=str)
    tags = GObject.Property(type=str)
    last_tag = GObject.Property(type=str)
    size = GObject.Property(type=str)


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/images_list_page.ui")
class ImagesListPage(Adw.NavigationPage):
    __gtype_name__ = "ImagesListPage"

    __gsignals__ = {"image-activated": (GObject.SignalFlags.RUN_FIRST, None, (object,))}

    content_box = Gtk.Template.Child()

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.build_ui()

    def build_ui(self) -> None:
        self.list_widget = AsyncList(
            provider=get_images,
            row_factory=self.render_row,
            search_placeholder=_("Search by short ID or tag"),
            search_callback=self.search,
            title=_("Images"),
        )

        self.content_box.append(self.list_widget)

    def render_row(self, image: Image) -> ImageRow:
        row = ImageRow(title=image.short_id)
        row.short_id = image.short_id
        row.tags = "".join(image.tags)
        row.last_tag = get_image_last_tag(image)
        row.size = humanize_size(get_image_size(image))
        row.set_activatable(True)
        row.connect("activated", self.on_row_clicked, image)

        if row.last_tag:
            last_tag = Badge(
                text=row.last_tag,
                style_class="tag-blue",
                margin_end=0,
            )

            row.add_suffix(last_tag)

        size = Badge(
            text=row.size,
            margin_end=12,
        )

        row.add_suffix(size)
        row.add_suffix(RowNext())

        return row

    def search(self, image: ImageRow, text: str) -> bool:
        return text.lower() in image.short_id or text.lower() in image.tags

    def on_row_clicked(self, _: AsyncList, image: Image) -> None:
        self.emit("image-activated", image)
