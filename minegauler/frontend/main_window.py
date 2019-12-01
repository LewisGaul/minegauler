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
import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QAction,
    QActionGroup,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QMenuBar,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from minegauler import core
from minegauler.utils import get_difficulty

from . import api, utils
from .minefield import MinefieldWidget
from .panel import PanelWidget


logger = logging.getLogger(__name__)


class BaseMainWindow(QMainWindow):
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
        self._icon: QIcon = QIcon(os.path.join(utils.IMG_DIR, "icon.ico"))
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
        # Keep track of all subwindows that are open.
        self._open_subwindows = {}

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
        ## GAME MENU
        exit_act = self._game_menu.addAction("Exit", self.close)
        exit_act.setShortcut("Alt+F4")

    # --------------------------------------------------------------------------
    # Qt method overrides
    # --------------------------------------------------------------------------
    # def show(self):   #@@@LG not sure if this will be needed either (resizing?)
    #     """Show the window."""
    #     super().show()

    def closeEvent(self, event):
        """
        Action to be performed when the window is closed. To allow the window
        to be closed, event.accept() should be called. This is provided by the
        PyQt class.

        Arguments:
        event (@@@)
            The event object, to be accepted if the window is to be closed.
        """
        event.accept()

    # --------------------------------------------------------------------------
    # Other methods
    # --------------------------------------------------------------------------
    def update_size(self):
        """Update the window size."""
        self._body_frame.adjustSize()
        self.centralWidget().adjustSize()
        self.adjustSize()


class MinegaulerGUI(BaseMainWindow):
    def __init__(
        self,
        ctrlr: api.AbstractController,
        gui_opts: utils.GuiOptsStruct = None,
        game_opts: core.utils.GameOptsStruct = None,
    ):
        """
        Arguments:
        ctrlr (Controller)
            The core controller.
        """
        self.ctrlr: api.AbstractController = ctrlr
        self.gui_opts: utils.GuiOptsStruct
        self.game_opts: core.utils.GameOptsStruct
        self._minefield_widget: MinefieldWidget

        if gui_opts:
            self.gui_opts = gui_opts.copy()
        else:
            self.gui_opts = utils.GuiOptsStruct(drag_select=False)
        if game_opts:
            self.game_opts = game_opts.copy()
        else:
            self.game_opts = core.utils.GameOptsStruct()

        # TODO: Something's not right, this should come first...
        super().__init__("MineGauler")

        self._panel_widget = PanelWidget(self, ctrlr, self.game_opts.mines)
        self._minefield_widget = MinefieldWidget(
            self,
            ctrlr,
            btn_size=self.gui_opts.btn_size,
            styles=self.gui_opts.styles,
            drag_select=self.gui_opts.drag_select,
        )
        self.set_panel_widget(self._panel_widget)
        self.set_body_widget(self._minefield_widget)

        # self._minefield_widget.at_risk_signal.connect(
        #     lambda: self._panel_widget.set_face("active")
        # )
        # self._minefield_widget.no_risk_signal.connect(
        #     lambda: self._panel_widget.set_face("ready")
        # )

        # cb_core.update_window_size.connect(self.update_size)
        # cb_core.change_mf_style.connect(self.update_style)

    def _populate_menubars(self):
        ## GAME MENU
        # Difficulty radiobuttons
        diff_group = QActionGroup(self, exclusive=True)
        for diff in ["Beginner", "Intermediate", "Expert", "Master"]:  # , 'Custom']:
            diff_act = QAction(diff, diff_group, checkable=True)
            self._game_menu.addAction(diff_act)
            diff_act.id = diff[0]
            if diff_act.id == get_difficulty(
                self.game_opts.x_size, self.game_opts.y_size, self.game_opts.mines
            ):
                diff_act.setChecked(True)
            diff_act.triggered.connect(
                lambda _: self._change_difficulty(diff_group.checkedAction().id)
            )
            diff_act.setShortcut(diff[0])

        self._game_menu.addSeparator()

        exit_act = self._game_menu.addAction("Exit", self.close)
        exit_act.setShortcut("Alt+F4")

        ## OPTIONS MENU
        # Drag select
        def toggle_drag_select():
            self.gui_opts.drag_select = not self.gui_opts.drag_select
            self._minefield_widget.drag_select = self.gui_opts.drag_select

        drag_act = self._opts_menu.addAction("Drag select", toggle_drag_select)
        drag_act.setCheckable(True)
        drag_act.setChecked(self.gui_opts.drag_select)

    def closeEvent(self, event):
        # cb_core.save_settings.emit()
        super().closeEvent(event)

    def _change_difficulty(self, id_: str) -> None:
        if id_ == "B":
            x, y, m = 8, 8, 10
        elif id_ == "I":
            x, y, m = 16, 16, 40
        elif id_ == "E":
            x, y, m = 30, 16, 99
        elif id_ == "M":
            x, y, m = 30, 30, 200
        else:
            raise ValueError(f"Unrecognised difficulty '{id_}'")

        self.ctrlr.resize_board(x_size=x, y_size=y, mines=m)
        self.update_size()

    def get_panel_widget(self) -> PanelWidget:
        return self._panel_widget

    def get_mf_widget(self) -> MinefieldWidget:
        return self._minefield_widget
