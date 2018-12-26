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

# from minegauler.types import GUIOptionsStruct
# from .utils import img_dir, CellImageType


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
        self.panel = widget
        
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
        self.body = widget
        
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
        self.footer = widget
        
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
    
    # def update_size(self):   #@@@LG not sure if this will be needed...
    #     """Update the window size."""
    #     self.panel_frame.adjustSize()
    #     self.body_frame.adjustSize()
    #     self.centralWidget().adjustSize()
    #     self.adjustSize()
        
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
    
    
class MinegaulerGUI(BaseMainWindow):
    def __init__(self, ctrlr, opts=None):
        """
        Arguments:
        ctrlr (Controller)
            The back-end controller.
        """
        # if opts:
        #     self.opts = opts
        # else:
        #     self.opts = GUIOptionsStruct()
        super().__init__('MineGauler')
        self.set_panel_widget(PanelWidget(self))
        self.set_body_widget(MinefieldWidget(self, ctrlr))
                                             # self.opts.btn_size,
                                             # self.opts.styles))
        # cb_core.update_window_size.connect(self.update_size)
        # cb_core.change_mf_style.connect(self.update_style)
        
    def closeEvent(self, event):
        # cb_core.save_settings.emit()
        super().closeEvent(event)