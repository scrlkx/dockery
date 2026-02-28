import threading
from typing import Any, Callable, List, Optional

from gi.repository import Adw, GLib, Gtk


class AsyncList(Gtk.Box):
    __gtype_name__ = "AsyncList"

    def __init__(
        self,
        provider: Callable[[], List[Any]],
        row_factory: Callable[[Any], Gtk.Widget],
        search_placeholder: str = "Search",
        search_callback: Optional[Callable[[Any, str], bool]] = None,
        search_enabled: bool = True,
        title: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)

        self.search_placeholder = search_placeholder
        self.provider = provider
        self.row_factory = row_factory
        self.search_callback = search_callback
        self.search_enabled = search_enabled
        self.title = title

        self.rows: List[Gtk.Widget] = []
        self.search_entry: Optional[Gtk.SearchEntry] = None
        self._load_generation: int = 0

        self.build_ui()
        self.load_content()

    def build_ui(self) -> None:
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_vexpand(True)

        self.stack = Gtk.Stack()
        self.stack.set_vexpand(True)
        self.append(self.stack)

        # Loading page
        spinner = Gtk.Spinner()
        spinner.set_spinning(True)
        spinner.set_halign(Gtk.Align.CENTER)
        spinner.set_size_request(48, 48)

        spinner_box = Gtk.Box()
        spinner_box.set_orientation(Gtk.Orientation.VERTICAL)
        spinner_box.set_vexpand(True)
        spinner_box.set_valign(Gtk.Align.CENTER)

        spinner_box.append(spinner)
        self.stack.add_named(spinner_box, "loading")

        # Content page
        content_container = Gtk.Box()
        content_container.set_orientation(Gtk.Orientation.VERTICAL)
        content_container.set_spacing(12)

        if self.search_enabled:
            self.search_entry = Gtk.SearchEntry()
            self.search_entry.set_placeholder_text(self.search_placeholder)
            self.search_entry.connect("search-changed", self.on_search_changed)
            content_container.append(self.search_entry)

        self.content_group = Adw.PreferencesGroup()

        if self.title:
            self.content_group.set_title(self.title)

        content_container.append(self.content_group)

        self.stack.add_named(content_container, "content")

        self.stack.set_visible_child_name("loading")

    def load_content(self) -> None:
        self._load_generation += 1
        generation = self._load_generation

        for row in self.rows:
            self.content_group.remove(row)

        self.rows.clear()

        self.stack.set_visible_child_name("loading")

        def task() -> None:
            items = self.provider()
            GLib.idle_add(self.on_content_load, items, generation)

        threading.Thread(target=task, daemon=True).start()

    def on_content_load(self, items: List[Any], generation: int) -> None:
        if generation != self._load_generation:
            return

        for item in items:
            row = self.row_factory(item)
            self.content_group.add(row)
            self.rows.append(row)

        self.stack.set_visible_child_name("content")

        if self.search_entry:
            self.on_search_changed(self.search_entry)

    def reload_content(self) -> None:
        self.load_content()

    def on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        text = entry.get_text().lower()

        if not self.search_callback:
            return

        for row in self.rows:
            row.set_visible(self.search_callback(row, text))
