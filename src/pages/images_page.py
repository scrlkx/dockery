from typing import Any, List

from gi.repository import Adw, GObject, Gtk

from ..components.badge import Badge
from ..utils.docker import get_image_architecture, get_image_size, get_images
from ..utils.ui import humanize_size


class ImageRow(Adw.ActionRow):
    __gtype_name__ = "ImageRow"

    name = GObject.Property(type=str)
    architecture = GObject.Property(type=str)
    size = GObject.Property(type=str)


@Gtk.Template(resource_path="/com/scrlkx/dockery/pages/images_page.ui")
class ImagesPage(Adw.NavigationPage):
    __gtype_name__ = "ImagesPage"

    search_entry = Gtk.Template.Child()
    images_group = Gtk.Template.Child()

    image_rows: List[ImageRow] = []

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        # self.register_events()
        self.build_ui()

    def build_ui(self) -> None:
        images = get_images()

        for image in images:
            row = ImageRow(title=image.tags[0])
            row.name = image.tags[0]
            row.architecture = get_image_architecture(image)
            row.size = humanize_size(get_image_size(image))

            row.set_activatable(True)

            self.image_rows.append(row)

            architecture = Badge(
                text=row.architecture,
                margin_end=12,
            )

            row.add_suffix(architecture)

            size = Badge(
                text=row.size,
                style_class="tag-blue",
                margin_end=12,
            )

            row.add_suffix(size)

            info = Gtk.Image.new_from_resource(
                "/com/scrlkx/dockery/icons/chevron-right.svg"
            )
            info.add_css_class("flat")

            row.add_suffix(info)

            self.images_group.add(row)
