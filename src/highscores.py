
import sys
import csv
import datetime as dt

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *


# List of highscores for settings:
#   difficulty='b'
#   max_per_cell=1
#   drag_select=True

# Attributes of each highscore are:
#   str name
#   int time (ms)
#   int 3bv
#   int date (s)


def import_highscores(settings=None):
    highscores = []
    with open('test.csv', 'r') as f:
        header1 = f.readline()
        # [Check header matches the settings]
        reader = csv.reader(f, escapechar='\\')
        key_order = reader.__next__()
        for row in reader:
            h = {key: row[i] for i, key in enumerate(key_order)}
            h['3bv'] = int(h['3bv'])
            h['time'] = int(h['time'])
            h['date'] = int(h['date'])
            h['3bv/s'] = '{:5.2f}'.format(1000 * h['3bv'] / h['time'] + 0.01)
            h['3bv'] = '{:2d}'.format(h['3bv'])
            h['time'] = '{:6.2f}'.format(int(h['time'] / 10) / 100 + 0.01)
            h['date'] = dt.date.fromtimestamp(h['date']).strftime('%d/%m/%Y')
            highscores.append(h)
    return highscores

def write_highscores(highscores, settings=None):
    key_order = ['name', 'time', '3bv', 'date']
    with open('test.csv', 'w', newline='') as f:
        # [Change to str of dict]
        f.write("difficulty='b',max_per_cell=1,drag_select=True\n")
        writer = csv.DictWriter(f, key_order, quoting=csv.QUOTE_NONE, escapechar='\\')
        writer.writeheader()
        writer.writerows(highscores)


class HighscoresWindow(QWidget):
    def __init__(self, parent, sort_by='time'):
        super().__init__(parent)
        self.setWindowTitle('Highscores')
        self.setupUI()
        self.sort(sort_by)
        self.show()
    def setupUI(self):
        lyt = QHBoxLayout(self)
        settings_frame = QFrame(self)
        lyt.addWidget(settings_frame)
        settings_frame.setLineWidth(2)
        # settings_frame.setFrameShadow(QFrame.Plain)
        settings_frame.setFrameShape(QFrame.StyledPanel)
        # Make highscores table
        self.hscores_table = table = QTableView()
        lyt.addWidget(table)
        model = HighscoresTableModel(table)
        table.setModel(model)
        table.setStyleSheet("""background: rgb(215,215,255);
                               font: normal 12px Sans-serif;""")
        table.resizeColumnsToContents()
        table.resizeRowsToContents()
        table.setAlternatingRowColors(True)
        table.setSelectionMode(QAbstractItemView.NoSelection)
        table.setFocusPolicy(Qt.NoFocus)
        table.setCornerButtonEnabled(False)
        table.setSortingEnabled(True)
        Hhead = table.horizontalHeader()
        Vhead = table.verticalHeader()
        Hhead.sortIndicatorChanged.connect(self.handleSortIndicatorChanged)
        Vhead.setSectionsClickable(False)
        Hhead.setSectionResizeMode(QHeaderView.Fixed)
        Vhead.setSectionResizeMode(QHeaderView.Fixed)
        width = Vhead.width() + 20
        for col in range(model.columnCount()):
            width += table.columnWidth(col)
        table.setFixedWidth(width)
        # Make settings/filter panel
        lyt = QVBoxLayout(settings_frame)
        settings_frame.setFixedSize(100, 100)
    def handleSortIndicatorChanged(self, col, order):
        """Set the sort indicator to match the actual sorting."""
        # If a column which shouldn't be sorted is selected, the indicator must
        #  be returned to the correct column
        model = self.hscores_table.model()
        header = self.hscores_table.horizontalHeader()
        key = model.headers[col]
        header.setSortIndicator(model.sort_index, Qt.DescendingOrder)
    def sort(self, key):
        headers = self.hscores_table.model().headers
        self.hscores_table.sortByColumn(headers.index(key), Qt.SortOrder())


class HighscoresTableModel(QAbstractTableModel):
    def __init__(self, parent):
        super().__init__(parent)
        self.headers = ['name', 'time', '3bv', '3bv/s', 'date']
        self.data = import_highscores() #list of dicts
    def rowCount(self, parent=None):
        return len(self.data)
    def columnCount(self, parent=None):
        return len(self.headers)
    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        elif role == Qt.DisplayRole:
            key = self.headers[index.column()]
            return QVariant(self.data[index.row()][key])
        elif role == Qt.TextAlignmentRole:
            if index.column() in [1, 3]:
                return QVariant(Qt.AlignRight | Qt.AlignVCenter)
            else:
                return QVariant(Qt.AlignHCenter | Qt.AlignVCenter)
        else:
            return QVariant()
    def headerData(self, num, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return QVariant(self.headers[num].capitalize())
        elif orientation == Qt.Vertical and role == Qt.DisplayRole:
            return QVariant(str(num + 1))
        return QVariant()
    def sort(self, col, order=None):
        """Sort table by given column number (order is ignored since sortable
        columns only have one direction to be sorted)."""
        key = self.headers[col]
        if key in ['name', '3bv', 'date']: #sorting not allowed
            return
        if key == 'time':
            order = Qt.AscendingOrder
        elif key == '3bv/s':
            # Order is backwards (higher is better)
            order = Qt.DescendingOrder
        # Store current sorting index and order
        self.sort_index = col
        # Perform the sort
        self.layoutAboutToBeChanged.emit()
        # Sort first by either time or 3bv/s, then by 3bv if there's a tie
        #  (higher 3bv higher for equal time, lower for equal 3bv/s)
        self.data.sort(
            key=lambda x:(float(x[self.headers[col]]), -float(x['3bv'])))
        if order == Qt.DescendingOrder:
            self.data.reverse()
        self.layoutChanged.emit()






if __name__ == '__main__':
    app = QApplication(sys.argv)
    hw = HighscoresWindow(None)
    app.exec_()
