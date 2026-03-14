"""UI overlay button for quickly zooming the plot to loaded geometry extents."""

from collections.abc import Callable
from pathlib import Path

import pyqtgraph as pg
from PyQt6.QtCore import QEvent, QObject, QSize, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QPushButton

_ASSETS_DIR = Path(__file__).parent / "assets"


class ZoomToDataButton(QObject):
    """Button overlay for zooming to data extents in the plot.
    
    Overlay button that triggers zooming to data when clicked.
    It is positioned in the bottom-right corner of the plot and
    adjusts its position on window resize or state changes.
    """

    def __init__(
        self, plot_widget: pg.PlotWidget, on_click: Callable[[], None]
    ) -> None:
        """Initializes the ZoomToDataButton."""
        super().__init__(plot_widget)
        self.plot_widget: pg.PlotWidget | None = plot_widget
        self.viewport = plot_widget.viewport()
        self.button = QPushButton("Zoom to Data", self.viewport)
        self.button.setIcon(QIcon(str(_ASSETS_DIR / "magnifying-glass.svg")))
        self.button.setIconSize(QSize(16, 16))
        self.button.setAutoDefault(False)
        self.button.setDefault(False)
        self.button.setEnabled(False)
        self.button.clicked.connect(on_click)
        self.button.adjustSize()

        self.viewport.installEventFilter(self)
        plot_widget.destroyed.connect(self._clear_references)
        self.viewport.destroyed.connect(self._clear_references)

    def setEnabled(self, enabled: bool) -> None:
        """Enables or disables the button.

        Args:
            enabled (bool): True to enable the button, False to disable it

        Returns:
            None
        """
        self.button.setEnabled(enabled)

    def schedule_reposition(self) -> None:
        """Schedule repositioning of button.
        
        Schedules the button to be repositioned on the next event loop cycle
        after Qt finishes processing current events and updating the layout.
        This ensures layout is ready.
        """
        QTimer.singleShot(0, self.reposition)

    # catches manual resize events
    def eventFilter(self, obj: QObject | None, event: QEvent | None) -> bool:
        """Listens for resize events on the viewport to reposition the button.

        Args:
            obj (QObject | None): The object that received the event
            event (QEvent | None): The event object to inspect

        Returns:
            bool: True if the event was handled, False otherwise
        """
        if (
            obj is self.viewport
            and event is not None
            and event.type() == QEvent.Type.Resize
        ):
            self.reposition()
        return super().eventFilter(obj, event)

    def reposition(self) -> None:
        """Repositions the button to the bottom-right corner of the viewport."""
        if self.plot_widget is None:
            return
        view_box = self.plot_widget.getPlotItem().getViewBox()
        scene_rect = view_box.sceneBoundingRect()
        bottom_right = self.plot_widget.mapFromScene(scene_rect.bottomRight())
        margin = 6
        self.button.move(
            bottom_right.x() - self.button.width() - margin,
            bottom_right.y() - self.button.height() - margin,
        )

    def _clear_references(self) -> None:
        """Clear widget references during teardown."""
        self.plot_widget = None
        self.viewport = None
