"""
app.py - Base GUI application implementation

April 2018, Lewis Gaul
"""

import sys
from os.path import join, dirname
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QFrame, QAction)

from .utils import img_dir


class MainWindow(QMainWindow):
    """
    Base class for the application.
    """
    PANEL_HEIGHT = 40
    PANEL_WIDTH_MIN = 140
    BODY_FRAME_WIDTH = 5
    ENTRYBAR_HEIGHT = 20
    
    def __init__(self, title=''):
        """
        Arguments:
          title='' (string)
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
        self.panel_frame.setFixedHeight(self.PANEL_HEIGHT)
        self.panel_frame.setMinimumWidth(self.PANEL_WIDTH_MIN)
        self.panel_frame.setFrameShadow(QFrame.Sunken)
        self.panel_frame.setFrameShape(QFrame.Panel)
        self.panel_frame.setLineWidth(2)
        vlayout.addWidget(self.panel_frame)
        # Main body widget config - use horizontal layout for centre alignment.
        hstretch = QHBoxLayout()
        hstretch.addStretch() #left-padding for centering
        self.body_frame = QFrame(central_widget)
        self.body_frame.setFrameShadow(QFrame.Raised)
        self.body_frame.setFrameShape(QFrame.Box)
        self.body_frame.setLineWidth(self.BODY_FRAME_WIDTH)
        hstretch.addWidget(self.body_frame)
        hstretch.addStretch() #right-padding for centering
        vlayout.addLayout(hstretch)
        
        # Name entry bar underneath the minefield
        self.entrybar_frame = QFrame(central_widget)
        self.entrybar_frame.setFixedHeight(self.ENTRYBAR_HEIGHT)
        vlayout.addWidget(self.entrybar_frame)
        
        self.init_menubar()
        
    def set_panel_widget(self, panel_widget):
        """
        Set the widget to occupy the top panel.
        Arguments:
          panel_widget (QWidget)
            The widget instance to place in the top panel.
        """
        lyt = QVBoxLayout(self.panel_frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(panel_widget)
        self.panel = panel_widget
        
    def set_body_widget(self, body_widget):
        """
        Set the widget to occupy the main section of the GUI.
        Arguments:
          body_widget (QWidget)
            The widget instance to place in the body.
        """
        lyt = QVBoxLayout(self.body_frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(body_widget)
        self.body = body_widget
        
    def set_entrybar_widget(self, entrybar_widget):
        """
        Set the widget to occupy the lower bar of the GUI.
        Arguments:
          entrybar_widget (QWidget)
            The widget instance to place in the lower bar.
        """
        lyt = QVBoxLayout(self.entrybar_frame)
        lyt.setContentsMargins(0, 0, 0, 0)
        lyt.addWidget(entrybar_widget)
        self.entrybar = entrybar_widget
        
    def init_menubar(self):
        """
        Initialise the menubar with 'Game', 'Options' and 'Help' menus, each
        accessible for adding actions to with 'Mainwindow.get_*_menu()'.
        """
        self.menubar = self.menuBar() #QMainWindow has QMenuBar already
        self.game_menu = self.menubar.addMenu('Game')
        self.opts_menu = self.menubar.addMenu('Options')
        self.help_menu = self.menubar.addMenu('Help')
        ## GAME MENU
        exit_act = self.game_menu.addAction('Exit', self.close)
        exit_act.setShortcut('Alt+F4')
        ## HELP MENU
    
    def get_game_menu(self):
        """
        Return: QMenuBar
            The game menu to which can have actions added to it.
        """
        return self.game_menu
    def get_options_menu(self):
        """
        Return: QMenuBar
            The options menu to which can have actions added to it.
        """
        return self.opts_menu
    def get_help_menu(self):
        """
        Return: QMenuBar
            The help menu to which can have actions added to it.
        """
        return self.help_menu
        
    def update_size(self):
        """
        Set the window to be a fixed size big enough to fit all of the widgets.
        """
        width = max(self.PANEL_WIDTH_MIN, self.body_frame.width())
        height = (self.menubar.height() + self.PANEL_HEIGHT
                  + self.body_frame.height() + self.ENTRYBAR_HEIGHT)
        self.setFixedSize(width, height)
        
    def show(self):
        """
        Show the window.
        """
        super().show()
        self.setFixedSize(self.width(), self.height())
        
    def closeEvent(self, event):
        """
        Action to be performed when the window is closed. To allow the window
        to be closed, event.accept() should be called. This is provided by the
        PyQt class.
        Arguments:
          event
            The event object to be accepted if the window is to be closed.
        """
        event.accept()
                   
                   
if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())