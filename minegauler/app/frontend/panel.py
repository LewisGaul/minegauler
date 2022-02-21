# April 2018, Lewis Gaul

"""
Widgets in the top panel.

Exports
-------
.. class:: PanelWidget
    Widget for the top panel of the Minegauler GUI.

"""

__all__ = ("PanelWidget",)

from typing import Optional, Union

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPalette, QPixmap
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from .. import paths
from ..shared.types import FaceState, GameState
from . import state


class PanelWidget(QWidget):
    """
    The panel widget.
    """

    clicked = pyqtSignal()

    def __init__(self, parent: Optional[QWidget], state_: state.State):
        """
        :param parent:
            Parent widget.
        :param state_:
            Shared frontend state.
        """
        super().__init__(parent)
        self._state: state.State = state_

        self.setFixedHeight(40)
        self.setMinimumWidth(120)

        self._mines_counter = _CounterWidget(self, self._state.mines)
        self._face_button = QLabel(self)
        self.timer = Timer(self)
        self.setup_ui()

    def setup_ui(self):
        """
        Set up the widgets contained in the panel.
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setAlignment(Qt.AlignCenter)
        # Mine counter widget.
        layout.addWidget(self._mines_counter)
        layout.addStretch()
        # Face button.
        self._face_button = QLabel(self)
        self._face_button.setFixedSize(32, 32)
        self._face_button.setFrameShape(QFrame.Panel)
        self._face_button.setFrameShadow(QFrame.Raised)
        self._face_button.setLineWidth(3)
        layout.addWidget(self._face_button)
        self.set_face(FaceState.READY)
        layout.addStretch()
        # Timer widget.
        layout.addWidget(self.timer.widget)

    # --------------------------------------------------------------------------
    # Qt method overrides
    # --------------------------------------------------------------------------
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self._face_button.setFrameShadow(QFrame.Sunken)

    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        if event.button() == Qt.LeftButton:
            self._face_button.setFrameShadow(QFrame.Raised)
            if self.rect().contains(event.pos()):
                self.clicked.emit()

    # --------------------------------------------------------------------------
    # Other methods
    # --------------------------------------------------------------------------
    def reset(self) -> None:
        """
        Reset the panel state.
        """
        self.update_game_state(GameState.READY)
        self.set_mines_counter(self._state.mines)
        self.timer.reset()

    def set_face(self, state: Union[FaceState, GameState, str]) -> None:
        """
        Arguments:
        state (str | GameState | FaceState)
        """
        try:
            state = state.value.lower()
        except AttributeError:
            pass
        life = 1
        fname = f"face{life}{state}.png"
        pixmap = QPixmap(str(paths.IMG_DIR / "faces" / fname))
        self._face_button.setPixmap(
            pixmap.scaled(26, 26, transformMode=Qt.SmoothTransformation)
        )

    def at_risk(self) -> None:
        if not self._state.game_status.finished():
            self.set_face(FaceState.ACTIVE)

    def no_risk(self) -> None:
        if not self._state.game_status.finished():
            self.set_face(FaceState.READY)

    def set_mines_counter(self, num: int) -> None:
        """
        This method is to be registered as a callback with a controller, as
        the widget itself can have no way of knowing how many mines are left to
        be found.
        """
        self._mines_counter.set_count(num)

    def update_game_state(self, state: GameState) -> None:
        """
        Receive an update from a backend.

        :param state:
            The new game state.
        """
        if state is GameState.ACTIVE:
            self.timer.start()
        elif state in {GameState.WON, GameState.LOST}:
            self.timer.stop()
            self.set_face(state)
        else:
            self.timer.reset()
            self.set_face(state)


class _CounterWidget(QLabel):
    """A widget template for the counters."""

    def __init__(self, parent: QWidget, count: int = 0):
        super().__init__(parent)
        self.setFrameShadow(QFrame.Sunken)
        self.setFrameShape(QFrame.Panel)
        self.setLineWidth(2)
        self.setFixedSize(39, 26)
        self.setAutoFillBackground(True)
        self.setAlignment(Qt.AlignCenter)
        self._palette = QPalette()
        self._palette.setColor(QPalette.Window, QColor("black"))
        self._palette.setColor(QPalette.WindowText, QColor("red"))
        self.setPalette(self._palette)
        self._font = QFont()
        self._font.setFamily("Helvetica")
        self._font.setPixelSize(13)
        self._font.setBold(True)
        self.setFont(self._font)
        self._count = count
        self.set_count(self._count)

    def set_count(self, count: int) -> None:
        """Set the value of the counter."""
        self.setText(f"{min(999, abs(count)):03d}")
        if count < 0:
            self._invert(False)
        else:
            self._invert(True)
        self._count = count

    def _invert(self, normal: bool = True) -> None:
        """Invert the colours."""
        if normal:
            self._palette.setColor(QPalette.Window, QColor("black"))
            self._palette.setColor(QPalette.WindowText, QColor("red"))
        else:
            self._palette.setColor(QPalette.Window, QColor("red"))
            self._palette.setColor(QPalette.WindowText, QColor("black"))
        self.setPalette(self._palette)


class Timer(QTimer):
    """A timer for the panel."""

    def __init__(self, parent):
        super().__init__()
        self.widget = _CounterWidget(parent)
        self.timeout.connect(self.update)
        self.seconds = 0

    # -------
    # Methods from parent class
    # -------
    def start(self):
        self.seconds = 1
        self.set_time(self.seconds)
        super().start(1000)  # Update every second

    def update(self):
        self.seconds += 1
        self.set_time(self.seconds)

    # -------
    # Public methods
    # -------
    def reset(self) -> None:
        """
        Reset the timer, stopping it if necessary.
        """
        self.stop()
        self.set_time(0)

    def set_time(self, seconds):
        self.widget.setText("{:03d}".format(min(seconds, 999)))
