"""
main_window.py - Base GUI application implementation

April 2018, Lewis Gaul

Exports:
BaseMainWindow
    Main window class.
    
MinegaulerGUI
    Minegauler main window class.
"""

import logging
from os.path import join

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QFrame, QAction, QActionGroup, QMenu, QSizePolicy)

from minegauler.frontend.minefield_widgets import MinefieldWidget
from minegauler.frontend.panel_widgets import PanelWidget
from minegauler.frontend.utils import img_dir
from minegauler.shared.utils import GUIOptsStruct, get_difficulty


logger = logging.getLogger(__name__)



class BaseMainWindow(QMainWindow):
    """
    Base class for the application implementing the general layout.
    """
    BODY_FRAME_WIDTH = 5
    
    def __init__(self, title=None):
        """
        Arguments:
          title=None (string | None)
            The window title.
        """
        super().__init__()
        self.setWindowTitle(title)
        self.icon = QIcon(join(img_dir, 'icon.ico'))
        self.setWindowIcon(self.icon)
        # Disable maximise button
        self.setWindowFlags(self.windowFlags() | Qt.CustomizeWindowHint)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowMaximizeButtonHint)
        self.setup_UI()
        self.init_menubars()
        # Keep track of all subwindows that are open.
        self.open_subwindows = {}

    # --------------------------------------------------------------------------
    # UI setup
    # --------------------------------------------------------------------------
    def setup_UI(self):
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
        self.panel_frame = QFrame(central_widget)
        self.panel_frame.setFrameShadow(QFrame.Sunken)
        self.panel_frame.setFrameShape(QFrame.Panel)
        self.panel_frame.setLineWidth(2)
        self.panel_frame.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        vlayout.addWidget(self.panel_frame)
        # Main body widget config - use horizontal layout for centre alignment.
        hstretch = QHBoxLayout()
        hstretch.addStretch() #left-padding for centering
        self.body_frame = QFrame(central_widget)
        self.body_frame.setFrameShadow(QFrame.Raised)
        self.body_frame.setFrameShape(QFrame.Box)
        self.body_frame.setLineWidth(self.BODY_FRAME_WIDTH)
        self.body_frame.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        hstretch.addWidget(self.body_frame)
        hstretch.addStretch() #right-padding for centering
        vlayout.addLayout(hstretch)
        
        # Name entry bar underneath the minefield
        self.footer_frame = QFrame(central_widget)
        vlayout.addWidget(self.footer_frame)
        
    def set_panel_widget(self, widget):
        """
        Set the widget to occupy the top panel.

        Arguments:
        widget (QWidget)
            The widget instance to place in the top panel.
        """
        lyt = QVBoxLayout(self.panel_frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(widget)
        self.panel_widget = widget
        
    def set_body_widget(self, widget):
        """
        Set the widget to occupy the main section of the GUI.

        Arguments:
        widget (QWidget)
            The widget instance to place in the body.
        """
        lyt = QVBoxLayout(self.body_frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(widget)
        self.body_widget = widget
        
    def set_footer_widget(self, widget):
        """
        Set the widget to occupy the lower bar of the GUI.

        Arguments:
        widget (QWidget)
            The widget instance to place in the lower bar.
        """
        lyt = QVBoxLayout(self.footer_frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(widget)
        self.footer_widget = widget
        
    def init_menubars(self):
        """
        Initialise the menubar with 'Game', 'Options' and 'Help' menus, each
        accessible for adding actions to with 'Mainwindow.get_*_menu()'.
        """
        self.menubar = self.menuBar()  # QMainWindow has QMenuBar already
        self.game_menu = self.menubar.addMenu('Game')
        self.opts_menu = self.menubar.addMenu('Options')
        self.help_menu = self.menubar.addMenu('Help')
        self.populate_menubars()
        
    def populate_menubars(self):
        ## GAME MENU
        exit_act = self.game_menu.addAction('Exit', self.close)
        exit_act.setShortcut('Alt+F4')

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
    def update_size(self):   #@@@LG not sure if this will be needed...
        """Update the window size."""
        self.panel_frame.adjustSize()
        self.body_frame.adjustSize()
        self.centralWidget().adjustSize()
        self.adjustSize()
    
    
class MinegaulerGUI(BaseMainWindow):
    def __init__(self, ctrlr, opts=None):
        """
        Arguments:
        ctrlr (Controller)
            The backend controller.
        """
        self.ctrlr = ctrlr
        if opts:
            self.opts = opts.copy()
        else:
            self.opts = GUIOptsStruct(drag_select=False)
        super().__init__('MineGauler')

        self.set_panel_widget(PanelWidget(self, ctrlr))
        self.minefield_widget = MinefieldWidget(
            self, ctrlr,
            btn_size=self.opts.btn_size,
            styles=self.opts.styles,
            drag_select=self.opts.drag_select)
        self.set_body_widget(self.minefield_widget)

        self.minefield_widget.at_risk_signal.connect(
            lambda: self.panel_widget.set_face('active'))
        self.minefield_widget.no_risk_signal.connect(
            lambda: self.panel_widget.set_face('ready'))

        # cb_core.update_window_size.connect(self.update_size)
        # cb_core.change_mf_style.connect(self.update_style)

    def populate_menubars(self):
        ## GAME MENU
        # Difficulty radiobuttons
        diff_group = QActionGroup(self, exclusive=True)
        for diff in ['Beginner', 'Intermediate', 'Expert', 'Master']:#, 'Custom']:
            diff_act = QAction(diff, diff_group, checkable=True)
            self.game_menu.addAction(diff_act)
            diff_act.id = diff[0]
            if diff_act.id == get_difficulty(self.ctrlr.opts.x_size,
                                             self.ctrlr.opts.y_size,
                                             self.ctrlr.opts.mines):
                diff_act.setChecked(True)
            diff_act.triggered.connect(
                lambda _: self._change_difficulty(
                    diff_group.checkedAction().id))
            diff_act.setShortcut(diff[0])

        self.game_menu.addSeparator()

        exit_act = self.game_menu.addAction('Exit', self.close)
        exit_act.setShortcut('Alt+F4')
        
    def closeEvent(self, event):
        # cb_core.save_settings.emit()
        super().closeEvent(event)

    def _change_difficulty(self, id):
        if id == 'B':
            x, y, m = 8, 8, 10
        elif id == 'I':
            x, y, m = 16, 16, 40
        elif id == 'E':
            x, y, m = 30, 16, 99
        elif id == 'M':
            x, y, m = 30, 30, 200

        self.minefield_widget.resize(x, y)
        self.update_size()
        self.ctrlr.resize_board(x_size=x, y_size=y, mines=m)