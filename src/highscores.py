"""Highscores are stored separately under filenames representing the settings
which group them. The first line of the file should match the filename, and if
this is not the case (for example if the file is edited) a warning will be
issued - note this is not used for checking validity of the highscores.
Each highscore is stored with a key which is used for checking validity."""


import sys
from os.path import join, exists
from shutil import move as movefile
import datetime as dt
import csv
import logging

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from utils import file_direc, calc_3bvps


# Store all highscores as they're imported in a dictionary of lists, with they
#  keys being the string representation of the settings.
all_highscores = {}
# For example:
# all_highscores = {'diff=b,drag_select=False,per_cell=1': [
#                      {'name':     'anon',     # str, len <= 12
#                       'time':     1234,       # int (ms)
#                       '3bv':      1,          # int
#                       'date':     1508000000, # int (timestamp)
#                       'flagging': 'NF',       # 'F' or 'NF'
#                       'key':      0,          # int
#                       }]
#                   }
# Store the number of imported highscores from each file to allow for only
#  appending new highscores while they're all stored together.
num_imported_highscores = {}
# For example:
# num_imported_highscores = {'diff=b,drag_select=False,per_cell=1': 10}

# Settings used to group highscores (in order for string representation)
settings_keys = ['diff', 'drag_select', 'per_cell']

# Encode highscore, takes settings str and highscore dict
# REMEMBER TO CHANGE THIS FOR OFFICIAL RELEASES BEFORE ENCRYPTING THE CODE
def enchs(s, h):
    if type(s) is not str:
        s = settings_to_str(s)
    return int(
        sum([412.12 * ord(c) for c in s]) +
        sum([688.99 * ord(c) for c in h['name']]) +
        200.34 * h['time'] +
        111.67 * h['3bv']
        )

def settings_to_str(settings):
    """Convert dictionary of settings to string. The dictionary can be passed
    directly as the argument, or an object containing the required attributes
    can be used."""
    if type(settings) is str:
        return settings
    if type(settings) is not dict:
        settings = {s: getattr(settings, s) for s in settings_keys}
    items = map(lambda k: f'{k}={settings[k]}', settings_keys)
    return ','.join(items)

def get_highscores(settings):
    settings = settings_to_str(settings)
    # If the file has already been read no need to read again, and there may be
    #  some new highscores which are stored in all_highscores and yet to be
    #  saved to the file.
    if settings in all_highscores:
        return all_highscores[settings]
    fpath = join(file_direc, f'{settings}.csv')
    if not exists(fpath):
        num_imported_highscores[settings] = 0
        all_highscores[settings] = []
        return all_highscores[settings]
    highscores = []
    with open(fpath, 'r') as f:
        # First line of file should be the settings
        header = f.readline()
        if header[:-1] != settings:
            logging.warn("First line of highscores file doesn't match filename")
        reader = csv.reader(f, escapechar='\\')
        # The second line contains the headers, giving the key order
        key_order = reader.__next__()
        for row in reader:
            h = {key: row[i] for i, key in enumerate(key_order)}
            for key in ['time', '3bv', 'date', 'key']:
                h[key] = int(h[key])
            if enchs(settings, h) == h['key']:# or True:
                highscores.append(h)
    all_highscores[settings] = highscores               #store highscores
    num_imported_highscores[settings] = len(highscores) #store number
    return highscores

def write_highscores(settings):
    """If file doesn't exist for these settings create it with expected
    headings. Append any new highscores to the file."""
    settings = settings_to_str(settings)
    key_order = ['name', 'time', '3bv', 'date', 'flagging', 'key']
    fpath = join(file_direc, f'{settings}.csv')
    if not exists(fpath):
        # Highscores file lost (deleted?) - save all
        num_imported_highscores[settings] = 0
        with open(fpath, 'w', newline='') as f:
            # Put settings as the top line to check it matches filename
            f.write(settings + '\n')
            # Write the headings, giving the key order
            writer = csv.DictWriter(f, key_order, quoting=csv.QUOTE_NONE,
                                    escapechar='\\')
            writer.writeheader()
    # Append new highscores to file
    with open(fpath, 'a', newline='') as f:
        writer = csv.DictWriter(f, key_order, quoting=csv.QUOTE_NONE,
                                escapechar='\\')
        new_hscores_start_index = num_imported_highscores[settings]
        hscores = all_highscores[settings][new_hscores_start_index:]
        writer.writerows(hscores)

def save_all_highscores():
    for key, hscores in all_highscores.items():
        if len(hscores) > num_imported_highscores[key]:
            write_highscores(key)

def get_hscore_position(hscore, settings, filters={}, cut_off=5):
    settings = settings_to_str(settings)
    highscores = []
    filters = {k: v for k, v in filters.items() if v}
    for h in all_highscores[settings]:
        all_pass = True
        for key, f in filters.items():
            if h[key].lower() != f.lower():
                all_pass = False
                break
        if all_pass:
            highscores.append(h) #all filters satisfied
    highscores.sort(key=lambda h: (h['time'], -h['3bv']))
    if hscore in highscores[:cut_off]:
        return 'time'
    highscores.sort(key=lambda h: (calc_3bvps(h), -h['3bv']), reverse=True)
    if hscore in highscores[:cut_off]:
        return '3bv/s'
    return None




class HighscoresWindow(QMainWindow):
    def __init__(self, parent, sort_by='time', filters={}):
        super().__init__(parent)
        self.gui = parent
        self.setWindowTitle('Highscores')
        self.view = QTableView()
        self.model = HighscoresModel(self, parent)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.setupUI()
        self.model.change_sort(sort_by)
        self.model.apply_filters(filters)
        self.filter_menu = None
        self.close_filter_menu = False
        self.show()
    def setupUI(self):
        lyt = QHBoxLayout(self.central_widget)
        # settings_frame = QFrame(self)
        # lyt.addWidget(settings_frame) #[currently not implemented]
        # settings_frame.setLineWidth(2)
        # settings_frame.setFrameShape(QFrame.StyledPanel)
        # Make highscores table
        lyt.addWidget(self.view)
        self.view.setModel(self.model)
        self.view.setStyleSheet("""background: rgb(215,215,255);
                                   font: normal 9pt Sans-serif;""")
        # self.view.resizeColumnsToContents()
        for col, size in enumerate([46, 37, 45, 68, 59]):
            self.view.setColumnWidth(col+1, size)
        self.view.resizeRowsToContents()
        self.view.setAlternatingRowColors(True)
        self.view.setSelectionMode(QAbstractItemView.NoSelection)
        self.view.setFocusPolicy(Qt.NoFocus)
        self.view.setCornerButtonEnabled(False)
        Hhead = self.view.horizontalHeader()
        Vhead = self.view.verticalHeader()
        Hhead.setSortIndicatorShown(True)
        Hhead.sortIndicatorChanged.connect(self.set_sort_indicator)
        Vhead.setSectionsClickable(False)
        # Fix width of all columns, let first column stretch to width
        Hhead.setSectionResizeMode(QHeaderView.Fixed)
        Hhead.setSectionResizeMode(0, QHeaderView.Stretch)
        # Fix height of rows
        Vhead.setDefaultSectionSize(22)
        Vhead.setSectionResizeMode(QHeaderView.Fixed)
        Hhead.sectionClicked.connect(self.handleHeaderClicked)
        self.view.setFixedWidth(400)
        # Make settings/filter panel
        # lyt = QVBoxLayout(settings_frame)
        # settings_frame.setFixedSize(200, 200)
    def set_sort_indicator(self, col=None, order=None):
        """Set the sort indicator to match the actual sorting."""
        # if col is None:
        col = self.model.sort_index
        # if order is None:
        order = Qt.DescendingOrder
        header = self.view.horizontalHeader()
        header.setSortIndicator(col, order)
    @pyqtSlot(int)
    def handleHeaderClicked(self, col):
        key = self.model.headers[col]
        if key in ['time', '3bv/s']:
            self.model.change_sort(key)
            return
        elif key not in ['name', 'flagging']:
            return
        #[Doesn't work...]
        # elif self.close_filter_menu == key:
        #     return
        self.filter_menu = QMenu(self)
        # def handleMenuHide():
        #     cursorPos = self.mapFromGlobal(QCursor().pos())
        #     print('menu hide', key)
        #     if self.view.horizontalHeader().rect().contains(cursorPos):
        #         print(self.view.horizontalHeader().rect())
        #         print(cursorPos)
        #         self.close_filter_menu = key
        # self.filter_menu.aboutToHide.connect(handleMenuHide)
        if key == 'flagging':
            def get_handle_filter(f):
                return lambda: self.model.apply_filters({'flagging': f})
            group = QActionGroup(self, exclusive=True)
            for action_num, action_name in enumerate(['All', 'F', 'NF']):
                action = QAction(action_name, group, checkable=True)
                if action_name == 'All':
                    action_name = ''
                if action_name == self.model.filters['flagging']:
                    action.setChecked(True)
                action.triggered.connect(get_handle_filter(action_name))
                self.filter_menu.addAction(action)
        elif key == 'name':
            # Make button for resetting filter (show all)
            all_action = QAction('All', checkable=True)
            if not self.model.filters['name']:
                all_action.setChecked(True)
            all_action.triggered.connect(
                                lambda: self.model.apply_filters({'name': ''}))
            self.filter_menu.addAction(all_action) #add to menu
            self.filter_menu.addSeparator() #patch highlighting with mouse movement
            ## Make entry bar for name filter
            # Create the entry bar with the existing filter as the text
            if self.model.filters['name']:
                text = self.model.filters['name']
            elif self.gui:
                text = self.gui.procr.name
            else:
                text = ''
            entry = QLineEdit(text, self)
            entry.selectAll() #select all the text
            # Set focus to the entry bar when the menu is opened
            self.filter_menu.aboutToShow.connect(entry.setFocus)
            def set_name_filter():
                # Emit signal for signal_mapper with text entered and hide menu
                self.model.apply_filters({'name': entry.text().strip()})
                # signal_mapper.mapped[str].emit(entry.text().strip())
                self.filter_menu.hide()
            entry.returnPressed.connect(set_name_filter) #enter applies filter
            name_action = QWidgetAction(self.filter_menu) #to contain QLineEdit
            name_action.setDefaultWidget(entry) #set widget on QWidgetAction
            self.filter_menu.addAction(name_action) #add to menu
        # Display menu in appropriate position, below header in column 'col'
        header = self.view.horizontalHeader()
        headerPos = self.view.mapToGlobal(header.pos())
        posY = headerPos.y() + header.height()
        posX = headerPos.x() + header.sectionPosition(col)
        pos = QPoint(posX, posY)
        self.close_filter_menu = False
        self.filter_menu.exec_(pos) #modal dialog


class HighscoresModel(QAbstractTableModel):
    """Handles the sorting and filtering of the group of highscores being
    displayed."""
    def __init__(self, parent, gui):
        super().__init__(parent)
        self.parent = parent
        self.gui = gui
        self.headers = ['name', 'time', '3bv', '3bv/s', 'date', 'flagging']
        self.disp_headers = [h.capitalize() for h in self.headers]
        self.all_data = [] #list of dicts
        self.displayed_data = [] #filled in the filter_and_sort method
        self.active_hscore = None
        self.sort_index = 1 #sort by time by default
        # Create dictionary of filters for each header
        self.filters = {h: '' for h in self.headers}
        self.old_sort_index = self.old_filters = None
    # Overwrite methods
    def rowCount(self, parent=None):
        return len(self.displayed_data)
    def columnCount(self, parent=None):
        return len(self.headers)
    def data(self, index, role):
        header = self.headers[index.column()]
        if not index.isValid():
            return QVariant()
        elif role == Qt.DisplayRole:
            return QVariant(self.format_data(index.row(), header))
        elif role == Qt.TextAlignmentRole:
            if header in ['time', '3bv/s']:
                return QVariant(Qt.AlignRight | Qt.AlignVCenter)
            else:
                return QVariant(Qt.AlignHCenter | Qt.AlignVCenter)
        elif role == Qt.FontRole and index.row() == self.get_active_row():
            bold_font = QFont('Sans-serif', 8)
            bold_font.setBold(True)
            return bold_font
        else:
            return QVariant()
    def headerData(self, index, orientation, role):
        bold_font = QFont('Sans-serif', 9)
        bold_font.setBold(True)
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                return QVariant(self.disp_headers[index])
            elif role == Qt.FontRole and (
                self.filters[self.headers[index]] or self.sort_index == index):
                return bold_font
        elif orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                return QVariant(str(index + 1))
            elif role == Qt.FontRole and index == self.get_active_row():
                return bold_font
        return QVariant()
    def apply_filters(self, filters, temp=False):
        if temp:
            self.old_filters = self.filters.copy() #store filters
        else:
            self.old_filters = None
        for h, f in filters.items():
            self.filters[h] = f
        self.filter_and_sort()
        if not temp and self.gui is not None:
            self.gui.set_highscore_settings(filters=self.filters)
    def change_sort(self, sort_by, temp=False):
        """Argument sort_by can be column index or header string."""
        if temp:
            self.old_sort_index = self.sort_index
        else:
            self.old_sort_index = None
        if type(sort_by) == int:
            self.sort_index = sort_by
            header = self.headers[sort_by]
        elif type(sort_by) == str:
            self.sort_index = self.headers.index(sort_by)
            header = sort_by
        self.parent.set_sort_indicator(self.sort_index)
        self.filter_and_sort()
        if not temp and self.gui is not None:
            self.gui.set_highscore_settings(sort_by=header)
    def update_hscores_group(self, settings):
        """
        Argument settings can be dictionary of settings or an object
        containing the required settings as attributes.
        """
        self.all_data = get_highscores(settings)
        self.filter_and_sort()
    def set_current_hscore(self, h):
        self.active_hscore = h
        if h is None:
            # Restore old sort order and filters on new game
            if self.old_sort_index:
                self.change_sort(self.old_sort_index)
            if self.old_filters:
                self.apply_filters(self.old_filters)
        #[Scroll to this hscore if get_active_row()]
        self.filter_and_sort()
    def get_active_row(self):
        if self.active_hscore in self.displayed_data:
            return self.displayed_data.index(self.active_hscore)
        else:
            return None
    def format_data(self, row, key):
        h = self.displayed_data[row]
        if key in ['name', 'flagging']:
            return h[key]
        elif key == 'time':
            # Truncate a digit of precision then convert to seconds and round up
            return '{:.2f}'.format((h[key] // 10) / 100 + 0.01)
        elif key == '3bv':
            return '{:3d}'.format(h[key]) #pad to 3 characters
        elif key == '3bv/s':
            return '{:.2f}'.format(calc_3bvps(h))
        elif key == 'date':
            return dt.date.fromtimestamp(h[key]).strftime('%d/%m/%y')
    def filter_and_sort(self):
        self.layoutAboutToBeChanged.emit()
        filters = {k: f for k, f in self.filters.items() if f}
        self.displayed_data = []
        for h in self.all_data:
            all_pass = True
            for key, f in filters.items():
                if h[key].lower() != f.lower():
                    all_pass = False
                    break
            if all_pass:
                self.displayed_data.append(h) #all filters satisfied
        # Sort first by either time or 3bv/s, then by 3bv if there's a tie
        #  (higher 3bv higher for equal time, lower for equal 3bv/s)
        if self.headers[self.sort_index] == 'time':
            self.displayed_data.sort(key=lambda h:(h['time'], -1 * h['3bv']))
        elif self.headers[self.sort_index] == '3bv/s':
            self.displayed_data.sort(
                key=lambda h:(calc_3bvps(h), -1 * h['3bv']), reverse=True)
        if 'name' not in filters:
            names = []
            i = 0
            while i < len(self.displayed_data):
                h = self.displayed_data[i]
                name = h['name'].lower()
                if name in names:
                    self.displayed_data.pop(i)
                else:
                    names.append(name)
                    i += 1
        self.layoutChanged.emit()





if __name__ == '__main__':
    app = QApplication(sys.argv)
    # from utils import default_settings
    settings = {'diff': 'b', 'drag_select': True, 'per_cell': 1}
    hw = HighscoresWindow(None)
    hw.model.update_hscores_group(settings)
    app.exec_()
