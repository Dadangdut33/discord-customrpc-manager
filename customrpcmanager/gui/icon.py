import qtawesome as qta
from PyQt6.QtCore import QSize


class IconManager:
    def __init__(self):
        # (widget, icon_name, size, color)
        self.bindings = []

    def set_icon(self, widget, name, size: int | None = None, color: str | None = None):
        icon = self._build_icon(name, color)
        widget.setIcon(icon)

        if size is not None:
            widget.setIconSize(QSize(size, size))

        self.bindings.append((widget, name, size, color))

    def refresh(self):
        qta.reset_cache()

        for widget, name, size, color in self.bindings:
            widget.setIcon(self._build_icon(name, color))

            if size is not None:
                widget.setIconSize(QSize(size, size))

    def _build_icon(self, name, color):
        if color is None:
            return qta.icon(name)  # theme aware
        return qta.icon(name, color=color)
