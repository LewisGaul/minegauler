"""
main_window.py - Base GUI application implementation

April 2018, Lewis Gaul

Exports:
BaseMainWindow
    Main window class.
    
MinegaulerGUI
    Minegauler main window class.
"""

__all__ = ("MinegaulerGUI",)

import logging
from typing import Callable, Dict, Optional, Type

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import core
from ..shared import highscores
from ..types import UIMode
from ..utils import GameOptsStruct, GuiOptsStruct, get_difficulty
from . import api, utils
from .highscores import HighscoresWindow
from .minefield import MinefieldWidget
from .panel import PanelWidget


logger = logging.getLogger(__name__)


class _BaseMainWindow(QMainWindow):
    """
    Base class for the application implementing the general layout.
    """

    BODY_FRAME_WIDTH = 5

    def __init__(
        self,
        title: Optional[str] = None,
        *,
        panel_widget: Optional[QWidget] = None,
        body_widget: Optional[QWidget] = None,
        footer_widget: Optional[QWidget] = None,
    ):
        """
        Arguments:
          title=None (string | None)
            The window title.
        """
        super().__init__()
        self._menubar: QMenuBar = self.menuBar()
        self._game_menu = self._menubar.addMenu("Game")
        self._opts_menu = self._menubar.addMenu("Options")
        self._help_menu = self._menubar.addMenu("Help")
        self._panel_frame: QFrame
        self._body_frame: QFrame
        self._footer_frame: QFrame
        self._panel_widget: Optional[QWidget] = panel_widget
        self._body_widget: Optional[QWidget] = body_widget
        self._footer_widget: Optional[QWidget] = footer_widget
        self._icon: QIcon = QIcon(str(utils.IMG_DIR / "icon.ico"))
        self.setWindowTitle(title)
        self.setWindowIcon(self._icon)
        # Disable maximise button
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        self._populate_menubars()
        self._setup_ui()
        if self._panel_widget is not None:
            self.set_panel_widget(self._panel_widget)
        if self._body_widget is not None:
            self.set_body_widget(self._body_widget)
        if self._footer_widget is not None:
            self.set_footer_widget(self._footer_widget)
        # Keep track of all non-modal subwindows that are open.
        self._open_subwindows: Dict[Type[QWidget], QWidget] = {}

    # --------------------------------------------------------------------------
    # UI setup
    # --------------------------------------------------------------------------
    def _setup_ui(self):
        """
        Set up the layout of the main window GUI.
        """
        # QMainWindow objects have a central widget to be set.
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        vlayout = QVBoxLayout(central_widget)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)
        # Top panel widget.
        self._panel_frame = QFrame(central_widget)
        self._panel_frame.setFrameShadow(QFrame.Sunken)
        self._panel_frame.setFrameShape(QFrame.Panel)
        self._panel_frame.setLineWidth(2)
        self._panel_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        vlayout.addWidget(self._panel_frame)
        # Main body widget config - use horizontal layout for centre alignment.
        hstretch = QHBoxLayout()
        hstretch.addStretch()  # left-padding for centering
        self._body_frame = QFrame(central_widget)
        self._body_frame.setFrameShadow(QFrame.Raised)
        self._body_frame.setFrameShape(QFrame.Box)
        self._body_frame.setLineWidth(self.BODY_FRAME_WIDTH)
        self._body_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hstretch.addWidget(self._body_frame)
        hstretch.addStretch()  # right-padding for centering
        vlayout.addLayout(hstretch)

        # Name entry bar underneath the minefield
        self._footer_frame = QFrame(central_widget)
        vlayout.addWidget(self._footer_frame)

    def set_panel_widget(self, widget: QWidget) -> None:
        """
        Set the widget to occupy the top panel.

        Arguments:
        widget (QWidget)
            The widget instance to place in the top panel.
        """
        lyt = QVBoxLayout(self._panel_frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(widget)
        self._panel_widget = widget

    def set_body_widget(self, widget: QWidget) -> None:
        """
        Set the widget to occupy the main section of the GUI.

        Arguments:
        widget (QWidget)
            The widget instance to place in the body.
        """
        lyt = QVBoxLayout(self._body_frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(widget)
        self._body_widget = widget

    def set_footer_widget(self, widget: QWidget) -> None:
        """
        Set the widget to occupy the lower bar of the GUI.

        Arguments:
        widget (QWidget)
            The widget instance to place in the lower bar.
        """
        lyt = QVBoxLayout(self._footer_frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(widget)
        self._footer_widget = widget

    def _populate_menubars(self):
        # GAME MENU
        exit_act = self._game_menu.addAction("Exit", self.close)
        exit_act.setShortcut("Alt+F4")

    # --------------------------------------------------------------------------
    # Other methods
    # --------------------------------------------------------------------------
    def update_size(self):
        """Update the window size."""
        self._body_frame.adjustSize()
        self.centralWidget().adjustSize()
        self.adjustSize()


class MinegaulerGUI(_BaseMainWindow):
    """The main Minegauler GUI window."""

    def __init__(
        self,
        ctrlr: api.AbstractSwitchingController,
        gui_opts: GuiOptsStruct = None,
        game_opts: GameOptsStruct = None,
    ):
        """
        :param ctrlr:
            The core controller.
        """
        self._ctrlr: api.AbstractSwitchingController = ctrlr
        self._gui_opts: GuiOptsStruct
        self._game_opts: GameOptsStruct  # TODO: This is wrong.

        if gui_opts:
            self._gui_opts = gui_opts.copy()
        else:
            self._gui_opts = GuiOptsStruct(drag_select=False)
        if game_opts:
            self._game_opts = game_opts.copy()
        else:
            self._game_opts = GameOptsStruct()

        # TODO: Something's not right, this should come first...
        super().__init__("MineGauler")

        self._panel_widget: PanelWidget = PanelWidget(
            self, ctrlr, self._game_opts.mines
        )
        self._minefield_widget: MinefieldWidget = MinefieldWidget(
            self,
            ctrlr,
            btn_size=self._gui_opts.btn_size,
            styles=self._gui_opts.styles,
            drag_select=self._gui_opts.drag_select,
        )
        self.set_panel_widget(self._panel_widget)
        self.set_body_widget(self._minefield_widget)

        self._minefield_widget.at_risk_signal.connect(self._panel_widget.at_risk)
        self._minefield_widget.no_risk_signal.connect(self._panel_widget.no_risk)

    def _populate_menubars(self) -> None:
        """Fill in the menubars."""

        # ----------
        # Game menu
        # ----------
        # New game (F2)
        new_game_act = self._game_menu.addAction("New game", self._ctrlr.new_game)
        new_game_act.setShortcut("F2")

        # Replay game (F3)
        replay_act = self._game_menu.addAction("Replay", self._ctrlr.restart_game)
        replay_act.setShortcut("F3")

        # Create board
        def switch_create_mode(checked: bool):
            mode = UIMode.CREATE if checked else UIMode.GAME
            self._ctrlr.switch_mode(mode)

        create_act = QAction("Create board", self, checkable=True, checked=False)
        self._game_menu.addAction(create_act)
        create_act.triggered.connect(switch_create_mode)

        # Save board

        # Load board

        self._game_menu.addSeparator()

        # Current info (F4)

        # Solver
        # - Probabilities (F5)
        # - Auto flag (Ctrl+F)
        # - Auto click (Ctrl+Enter)

        # Highscores (F6)
        def open_highscores():
            try:
                settings = self._ctrlr.get_highscore_settings()
            except AttributeError:
                logger.exception("Unable to get highscore settings")
                settings = highscores.HighscoreSettingsStruct("B", 1)
            self.open_highscores_window(settings)

        highscores_act = self._game_menu.addAction("Highscores", open_highscores)
        highscores_act.setShortcut("F6")

        # Stats (F7)

        self._game_menu.addSeparator()

        # Difficulty radiobuttons
        # - Beginner (b)
        # - Intermediate (i)
        # - Expert (e)
        # - Master (m)
        # - Custom (c)
        diff_group = QActionGroup(self)
        diff_group.setExclusive(True)
        for diff in ["Beginner", "Intermediate", "Expert", "Master", "Custom"]:
            diff_act = QAction(diff, diff_group, checkable=True)
            self._game_menu.addAction(diff_act)
            diff_act.id = diff[0]
            if diff_act.id == get_difficulty(
                self._game_opts.x_size, self._game_opts.y_size, self._game_opts.mines
            ):
                diff_act.setChecked(True)
            diff_act.triggered.connect(
                lambda _: self._change_difficulty(diff_group.checkedAction().id)
            )
            diff_act.setShortcut(diff[0])

        self._game_menu.addSeparator()

        # Zoom

        # Styles
        # - Buttons
        # - Images
        # - Numbers

        # self._game_menu.addSeparator()

        # Exit (F4)
        self._game_menu.addAction("Exit", self.close, shortcut="Alt+F4")

        # ----------
        # Options menu
        # ----------
        # First-click success
        def toggle_first_success():
            self._game_opts.first_success = not self._game_opts.first_success
            self._ctrlr.set_first_success(self._game_opts.first_success)

        first_act = QAction(
            "Safe start", self, checkable=True, checked=self._game_opts.first_success
        )
        self._opts_menu.addAction(first_act)
        first_act.triggered.connect(toggle_first_success)

        # Drag select
        def toggle_drag_select():
            self._gui_opts.drag_select = not self._gui_opts.drag_select
            self._minefield_widget.drag_select = self._gui_opts.drag_select

        drag_act = self._opts_menu.addAction("Drag select", toggle_drag_select)
        drag_act.setCheckable(True)
        drag_act.setChecked(self._gui_opts.drag_select)

        # Max mines per cell option
        def get_change_per_cell_func(n):
            def change_per_cell():
                self._game_opts.per_cell = n
                self._ctrlr.set_per_cell(n)

            return change_per_cell

        per_cell_menu = self._opts_menu.addMenu("Max per cell")
        per_cell_group = QActionGroup(self)
        per_cell_group.setExclusive(True)
        for i in range(1, 4):

            action = QAction(str(i), self, checkable=True)
            per_cell_menu.addAction(action)
            per_cell_group.addAction(action)
            if self._game_opts.per_cell == i:
                action.setChecked(True)
            action.triggered.connect(get_change_per_cell_func(i))

        # ----------
        # Help menu
        # ----------
        # TODO: None yet...

    def _change_difficulty(self, id_: str) -> None:
        if id_ == "B":
            x, y, m = 8, 8, 10
        elif id_ == "I":
            x, y, m = 16, 16, 40
        elif id_ == "E":
            x, y, m = 30, 16, 99
        elif id_ == "M":
            x, y, m = 30, 30, 200
        elif id_ == "C":
            logger.info("Opening popup window for selecting custom board")
            self._open_custom_board_modal()
            return
        else:
            raise ValueError(f"Unrecognised difficulty '{id_}'")

        self._ctrlr.resize_board(x_size=x, y_size=y, mines=m)
        self.update_size()

    def _open_custom_board_modal(self) -> None:
        _CustomBoardModal(
            self,
            self._game_opts.x_size,
            self._game_opts.y_size,
            self._game_opts.mines,
            self._ctrlr.resize_board,
        ).show()

    def get_panel_widget(self) -> PanelWidget:
        return self._panel_widget

    def get_mf_widget(self) -> MinefieldWidget:
        return self._minefield_widget

    def update_game_opts(self, **kwargs) -> None:
        """Update the stored game options."""
        # TODO: Should this API even exist? :/
        for k, v in kwargs.items():
            setattr(self._game_opts, k, v)

    def get_gui_opts(self) -> GuiOptsStruct:
        return self._gui_opts

    def open_highscores_window(
        self, settings: highscores.HighscoreSettingsStruct
    ) -> None:
        self._open_subwindows["highscores"] = HighscoresWindow(settings)
        self._open_subwindows["highscores"].show()


class _CustomBoardModal(QDialog):
    """A popup window to select custom board dimensions."""

    def __init__(
        self, parent: QWidget, cols: int, rows: int, mines: int, callback: Callable
    ):
        super().__init__(parent)
        self.setWindowTitle("Custom")
        self._cols: int = cols
        self._rows: int = rows
        self._mines: int = mines
        self._callback: Callable = callback
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self) -> None:
        """Set up the UI."""
        base_layout = QVBoxLayout(self)
        base_layout.addWidget(
            QLabel("Select the number of rows, columns and mines.", self)
        )

        # Set up the input sliders and spin boxes.
        grid_layout = QGridLayout()
        base_layout.addLayout(grid_layout)

        def make_row(
            row: int, label: str, current: int, minval: int, maxval: int
        ) -> _SliderSpinner:
            grid_layout.addWidget(QLabel(label, self), row, 0)
            slider = _SliderSpinner(self)
            grid_layout.addWidget(slider, row, 1)
            slider.setValue(current)
            slider.setMinimum(minval)
            slider.setMaximum(maxval)
            return slider

        y_slider = make_row(1, "Rows", self._rows, 2, 50)
        x_slider = make_row(2, "Columns", self._cols, 2, 50)
        m_slider = make_row(3, "Mines", self._mines, 1, self._rows * self._cols - 1)

        def set_mines_max():
            m_slider.setMaximum(x_slider.value() * y_slider.value() - 1)

        x_slider.valueChanged.connect(set_mines_max)
        y_slider.valueChanged.connect(set_mines_max)

        # Ok/Cancel buttons.
        def ok_pressed():
            self._callback(x_slider.value(), y_slider.value(), m_slider.value())
            self.close()

        ok_btn = QPushButton("Ok", self)
        ok_btn.pressed.connect(ok_pressed)
        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.pressed.connect(self.close)
        btns_layout = QHBoxLayout()
        base_layout.addLayout(btns_layout)
        btns_layout.addWidget(ok_btn)
        btns_layout.addWidget(cancel_btn)


class _SliderSpinner(QWidget):
    """A combination of a slider and a spinbox."""

    valueChanged = pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slider = QSlider(Qt.Horizontal)
        self.numbox = QSpinBox()
        self.numbox.setRange(self.slider.minimum(), self.slider.maximum())
        self.numbox.setFixedWidth(50)
        self.slider.valueChanged.connect(self.numbox.setValue)
        self.slider.rangeChanged.connect(self.numbox.setRange)
        self.numbox.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self.valueChanged.emit)
        self.valueChanged.connect(self.setValue)
        layout = QHBoxLayout(self)
        layout.addWidget(self.slider)
        layout.addWidget(self.numbox)

    def setMinimum(self, minval: int):
        self.slider.setMinimum(minval)

    def setMaximum(self, maxval: int):
        self.slider.setMaximum(maxval)

    def setValue(self, value: int):
        self.slider.setValue(value)

    def value(self) -> int:
        return self.slider.value()


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    widget = _CustomBoardModal(None, 10, 20, 30, lambda x, y, z: print(x, y, z))
    app.exec()
