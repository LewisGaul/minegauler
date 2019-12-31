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
import traceback
from typing import Callable, Dict, Mapping, Optional, Type

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QFocusEvent, QFont, QIcon, QKeyEvent
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import shared
from ..core import api
from ..shared.highscores import HighscoreSettingsStruct, HighscoreStruct
from ..shared.utils import GUIOptsStruct, get_difficulty
from ..types import CellContentsType, CellImageType, GameState, UIMode
from ..typing import Coord_T
from . import highscores, minefield, panel, state, utils


logger = logging.getLogger(__name__)


class _BaseMainWindow(QMainWindow):
    """
    Base class for the application implementing the general layout.
    """

    BODY_FRAME_WIDTH = 10

    def __init__(self, parent: Optional[QWidget], title: Optional[str] = None):
        """
        :param title:
            The window title.
        """
        super().__init__(parent)
        self._menubar: QMenuBar = self.menuBar()
        self._game_menu = self._menubar.addMenu("Game")
        self._opts_menu = self._menubar.addMenu("Options")
        self._help_menu = self._menubar.addMenu("Help")
        self._panel_frame: QFrame
        self._body_frame: QFrame
        self._footer_frame: QFrame
        self._panel_widget: Optional[QWidget]
        self._body_widget: Optional[QWidget]
        self._footer_widget: Optional[QWidget]
        self._icon: QIcon = QIcon(str(utils.IMG_DIR / "icon.ico"))
        self.setWindowTitle(title)
        self.setWindowIcon(self._icon)
        # Disable maximise button
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        self._setup_ui()
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
        central_widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.setCentralWidget(central_widget)
        vlayout = QVBoxLayout(central_widget)
        vlayout.setContentsMargins(0, 0, 0, 0)
        vlayout.setSpacing(0)
        # Top panel widget.
        self._panel_frame = QFrame(central_widget)
        self._panel_frame.setFrameShadow(QFrame.Sunken)
        self._panel_frame.setFrameShape(QFrame.Panel)
        self._panel_frame.setLineWidth(2)
        self._panel_frame.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)
        vlayout.addWidget(self._panel_frame)
        # Main body widget config - use horizontal layout for centre alignment.
        hstretch = QHBoxLayout()
        hstretch.addStretch()  # left-padding for centering
        self._body_frame = QFrame(central_widget)
        self._body_frame.setFrameShadow(QFrame.Raised)
        self._body_frame.setFrameShape(QFrame.Box)
        self._body_frame.setLineWidth(self.BODY_FRAME_WIDTH / 2)
        # self._body_frame.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
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


class _MinegaulerGUIMeta(type(api.AbstractListener), type(_BaseMainWindow)):
    """Combined metaclass for the MinegaulerGUI class."""


class MinegaulerGUI(
    api.AbstractListener, _BaseMainWindow, metaclass=_MinegaulerGUIMeta
):
    """The main Minegauler GUI window."""

    def __init__(
        self, ctrlr: api.AbstractSwitchingController, initial_state: state.State
    ):
        """
        :param ctrlr:
            The core controller.
        :param initial_state:
            Initial application state.
        """
        super().__init__(None, "Minegauler")
        self._ctrlr: api.AbstractSwitchingController = ctrlr
        self._state: state.State = initial_state.deepcopy()

        self._panel_widget = panel.PanelWidget(self, self._state)
        self._mf_widget = minefield.MinefieldWidget(self, self._ctrlr, self._state)
        self._populate_menubars()
        self.set_panel_widget(self._panel_widget)
        self.set_body_widget(self._mf_widget)
        self._name_entry_widget = _NameEntryBar(self, self._state.name)
        self.set_footer_widget(self._name_entry_widget)
        self._update_size()

        self._panel_widget.clicked.connect(self._ctrlr.new_game)
        self._mf_widget.at_risk_signal.connect(self._panel_widget.at_risk)
        self._mf_widget.no_risk_signal.connect(self._panel_widget.no_risk)
        self._name_entry_widget.name_updated_signal.connect(self._set_name)

    # ----------------------------------
    # Implemented abstractmethods
    # ----------------------------------
    def reset(self) -> None:
        """
        Called to indicate the GUI state should be soft-reset.

        This is distinct from a factory reset (settings are not changed).
        """
        self._panel_widget.reset()
        self._mf_widget.reset()

    def resize_minefield(self, x_size: int, y_size: int) -> None:
        """
        Called to indicate the board shape has changed.

        :param x_size:
            The number of columns.
        :param y_size:
            The number of rows.
        """
        self._state.x_size = x_size
        self._state.y_size = y_size
        self._mf_widget.reshape(x_size, y_size)

    def set_mines(self, mines: int) -> None:
        """
        Called to indicate the base number of mines has changed.

        :param mines:
            The number of mines.
        """
        self._state.mines = mines

    def update_cells(self, cell_updates: Mapping[Coord_T, CellContentsType]) -> None:
        """
        Called to indicate some cells have changed state.

        :param cell_updates:
            A mapping of cell coordinates to their new state.
        """
        for c, state in cell_updates.items():
            self._mf_widget.set_cell_image(c, state)

    def update_game_state(self, game_state: GameState) -> None:
        """
        Called to indicate the game state has changed.

        :param game_state:
            The new game state.
        """
        self._state.game_status = game_state
        if game_state is GameState.READY:
            self._state.highscores_state.current_highscore = None
        self._panel_widget.update_game_state(game_state)

    def update_mines_remaining(self, mines_remaining: int) -> None:
        """
        Called to indicate the number of remaining mines has changed.

        :param mines_remaining:
            The remaining number of mines.
        """
        self._panel_widget.set_mines_counter(mines_remaining)

    def handle_finished_game(self, info: api.EndedGameInfo) -> None:
        """
        Called once when a game ends.

        :param info:
            A store of end-game information.
        """
        self._panel_widget.timer.stop()
        self._panel_widget.timer.set_time(int(info.elapsed + 1))
        # Store the highscore if the game was won.
        if (
            info.game_state is GameState.WON
            and info.difficulty != "C"
            and not info.minefield_known
        ):
            highscore = HighscoreStruct(
                difficulty=info.difficulty,
                per_cell=info.per_cell,
                timestamp=int(info.start_time),
                elapsed=info.elapsed,
                bbbv=info.bbbv,
                bbbvps=info.bbbv / info.elapsed,
                drag_select=self._state.drag_select,
                name=self._state.name,
                flagging=info.flagging,
            )
            shared.highscores.insert_highscore(highscore)
            self._state.highscores_state.current_highscore = highscore
            # Check whether to pop up the highscores window.
            new_best = shared.highscores.is_highscore_new_best(highscore)
            if new_best:
                self.open_highscores_window(highscore, new_best)

    def handle_exception(self, method: str, exc: Exception) -> None:
        logger.error(
            "Error occurred when calling %s() from backend:\n%s\n%s",
            method,
            "".join(traceback.format_exception(None, exc, exc.__traceback__)),
            exc,
        )
        raise RuntimeError(exc).with_traceback(exc.__traceback__)

    # --------------------------------------------------------------------------
    # Qt method overrides
    # --------------------------------------------------------------------------
    def sizeHint(self) -> QSize:
        width = max(
            self._body_frame.sizeHint().width(),
            self._panel_frame.minimumSizeHint().width(),
        )
        height = (
            self._menubar.sizeHint().height()
            + self._panel_frame.sizeHint().height()
            + self._body_frame.sizeHint().height()
            + self._name_entry_widget.sizeHint().height()
        )
        return QSize(width, height)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._name_entry_widget.clearFocus()

    # --------------------------------------------------------------------------
    # Other methods
    # --------------------------------------------------------------------------
    def _update_size(self):
        """Update the window size."""
        self.setFixedSize(self.sizeHint())

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
            self._state.ui_mode = mode
            self._ctrlr.switch_mode(mode)

        create_act = QAction(
            "Create board",
            self,
            checkable=True,
            checked=self._state.ui_mode is UIMode.CREATE,
        )
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
        highscores_act = self._game_menu.addAction(
            "Highscores", self.open_highscores_window
        )
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
                self._state.x_size, self._state.y_size, self._state.mines
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
        def get_change_style_func(grp, style):
            def change_style():
                self._state.styles[grp] = style
                self._mf_widget.update_style(grp, style)

            return change_style

        styles_menu = QMenu("Styles", self)
        self._game_menu.addMenu(styles_menu)
        for img_group in [CellImageType.BUTTONS]:
            img_group_name = img_group.name.capitalize()
            submenu = QMenu(img_group_name, self)
            styles_menu.addMenu(submenu)
            group = QActionGroup(self, exclusive=True)
            for folder in (utils.IMG_DIR / img_group_name).glob("*"):
                style = folder.name
                style_act = QAction(style, self, checkable=True)
                if style == self._state.styles[img_group]:
                    style_act.setChecked(True)
                group.addAction(style_act)
                style_act.triggered.connect(get_change_style_func(img_group, style))
                submenu.addAction(style_act)

        self._game_menu.addSeparator()

        # Exit (F4)
        self._game_menu.addAction("Exit", self.close, shortcut="Alt+F4")

        # ----------
        # Options menu
        # ----------
        # First-click success
        def toggle_first_success():
            new_val = not self._state.pending_first_success
            self._state.first_success = new_val
            self._ctrlr.set_first_success(new_val)

        first_act = QAction(
            "Safe start", self, checkable=True, checked=self._state.first_success
        )
        self._opts_menu.addAction(first_act)
        first_act.triggered.connect(toggle_first_success)

        # Drag select
        drag_act = self._opts_menu.addAction(
            "Drag select",
            lambda: setattr(
                self._state, "drag_select", not self._state.pending_drag_select
            ),
        )
        drag_act.setCheckable(True)
        drag_act.setChecked(self._state.drag_select)

        # Max mines per cell option
        def get_change_per_cell_func(n):
            def change_per_cell():
                self._state.per_cell = n
                self._ctrlr.set_per_cell(n)

            return change_per_cell

        per_cell_menu = self._opts_menu.addMenu("Max per cell")
        per_cell_group = QActionGroup(self)
        per_cell_group.setExclusive(True)
        for i in range(1, 4):
            action = QAction(str(i), self, checkable=True)
            per_cell_menu.addAction(action)
            per_cell_group.addAction(action)
            if self._state.per_cell == i:
                action.setChecked(True)
            action.triggered.connect(get_change_per_cell_func(i))

        # ----------
        # Help menu
        # ----------
        # TODO: None yet...

    def _change_difficulty(self, id_: str) -> None:
        """
        Change the difficulty via the core controller.

        :param id_:
            The difficulty ('b', 'i', 'e', 'm' or 'c').
        """
        id_ = id_.upper()
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
        self._update_size()

    def _set_name(self, name: str) -> None:
        self._state.name = name
        self._state.highscores_state.name_hint = name

    def _open_custom_board_modal(self) -> None:
        """Open the modal popup to select the custom difficulty."""

        def callback(x, y, m):
            self._ctrlr.resize_board(x, y, m)
            self._update_size()

        _CustomBoardModal(
            self, self._state.x_size, self._state.y_size, self._state.mines, callback
        ).show()

    def get_gui_opts(self) -> GUIOptsStruct:
        return GUIOptsStruct.from_structs(self._state, self._state.pending_game_state)

    def open_highscores_window(
        self,
        settings: Optional[HighscoreSettingsStruct] = None,
        sort_by: Optional[str] = None,
    ) -> None:
        """
        Open the highscores window.

        :param settings:
            Optionally specify the highscore settings to display highscores
            for. By default the current frontend state is used.
        :param sort_by:
            Optionally specify the key to sort the highscores by. Defaults to
            the previous sort key.
        """
        if self._open_subwindows.get("highscores"):
            self._open_subwindows.get("highscores").close()
        if not settings:
            settings = HighscoreSettingsStruct(
                difficulty=get_difficulty(
                    self._state.x_size, self._state.y_size, self._state.mines
                ),
                per_cell=self._state.per_cell,
                drag_select=self._state.drag_select,
            )
        if sort_by:
            self._state.highscores_state.sort_by = sort_by
        self._state.highscores_state.name_hint = self._state.name
        win = highscores.HighscoresWindow(self, settings, self._state.highscores_state)
        win.show()
        self._open_subwindows["highscores"] = win


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


class _NameEntryBar(QLineEdit):
    """Entry bar for entering a name."""

    name_updated_signal = pyqtSignal(str)

    def __init__(self, parent, text: str = ""):
        super().__init__(parent)
        self.setText(text)
        self.setPlaceholderText("Name")
        self.setAlignment(Qt.AlignCenter)
        font = QFont("Helvetica")
        font.setBold(True)
        self.setFont(font)

    def keyPressEvent(self, event: QKeyEvent):
        super().keyPressEvent(event)
        if event.key() in [Qt.Key_Return, Qt.Key_Enter]:
            self.clearFocus()

    def focusOutEvent(self, event: QFocusEvent):
        super().focusOutEvent(event)
        self.setText(self.text().strip())
        logger.info("Setting name to %r", self.text())
        self.name_updated_signal.emit(self.text())


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    widget = _CustomBoardModal(None, 10, 20, 30, lambda x, y, z: print(x, y, z))
    widget.show()
    app.exec()
