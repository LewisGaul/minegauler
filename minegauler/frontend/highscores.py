"""
highscores.py - Highscores window implementation

July 2018, Lewis Gaul
"""

__all__ = ("HighscoresWindow",)

import logging
import sys
import time as tm
from typing import Dict, List, Optional

from PyQt5.QtCore import (
    QAbstractTableModel,
    QPoint,
    QRect,
    QSize,
    Qt,
    QVariant,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtGui import QCursor, QFont, QHideEvent
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QAbstractScrollArea,
    QAction,
    QActionGroup,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMenu,
    QTableView,
    QWidget,
    QWidgetAction,
)

from ..shared import highscores, utils
from . import state


logger = logging.getLogger(__name__)


class HighscoresWindow(QDialog):
    """A standalone highscores window."""

    def __init__(
        self,
        parent: Optional[QWidget],
        settings: highscores.HighscoreSettingsStruct,
        state_: state.HighscoreWindowState,
    ):
        super().__init__(parent)
        self._state = state_
        self.setWindowTitle("Highscores")
        self._model = HighscoresModel(self, self._state)
        self._table = HighscoresTable(self._model, self._state)
        self.setup_ui()
        self._model.sort_changed.connect(self._table.set_sort_indicator)
        self._table.add_filter.connect(self.set_filter)
        self._model.update_highscores_group(settings)

    def setup_ui(self) -> None:
        lyt = QHBoxLayout(self)
        # settings_frame = QFrame(self)
        # lyt.addWidget(settings_frame) #[currently not implemented]
        # settings_frame.setLineWidth(2)
        # settings_frame.setFrameShape(QFrame.StyledPanel)
        # Make highscores table.
        lyt.addWidget(self._table)
        # Make settings/filter panel.
        # lyt = QVBoxLayout(settings_frame)
        # settings_frame.setFixedSize(200, 200)

    def keyPressEvent(self, event):
        """Override the QWidget method for receiving key presses."""
        # Make enter/return/escape close the window.
        if event.key() in [Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape]:
            self.close()
        else:
            super().keyPressEvent(event)

    @pyqtSlot(str, str)
    def set_filter(self, filter_by: str, filter: str) -> None:
        if filter_by == "name":
            self._state.name_filter = filter
        elif filter_by == "flagging":
            self._state.flagging_filter = filter
        else:
            raise ValueError(f"Unrecognised header to filter by: '{filter_by}'")
        self._model.filter_and_sort()


class HighscoresModel(QAbstractTableModel):
    """Model handling sorting and filtering of a highscore group."""

    sort_changed = pyqtSignal(int)
    headers = ["name", "time", "3bv", "3bv/s", "date", "flagging"]

    def __init__(self, parent: Optional[QWidget], state_: state.HighscoreWindowState):
        super().__init__(parent)
        self._state: state.HighscoreWindowState = state_
        self._all_data: List[highscores.HighscoreStruct] = []
        self._displayed_data: List[highscores.HighscoreStruct] = []

    @property
    def _filters(self) -> Dict[str, Optional[str]]:
        return {
            "name": self._state.name_filter,
            "flagging": self._state.flagging_filter,
        }

    # -------------------------------------------------------------------------
    # Implement abstract methods
    # -------------------------------------------------------------------------
    def rowCount(self, parent=None):
        return len(self._displayed_data)

    def columnCount(self, parent=None):
        return len(self.headers)

    def data(self, index, role):
        header = self.headers[index.column()]
        if not index.isValid():
            return QVariant()
        elif role == Qt.DisplayRole:
            return QVariant(self.format_data(index.row(), header))
        elif role == Qt.TextAlignmentRole:
            return QVariant(Qt.AlignHCenter | Qt.AlignVCenter)
        elif role == Qt.FontRole:
            bold_font = QFont("Sans-serif", 8)
            bold_font.setBold(True)
            if index.row() == self.get_active_row():
                return bold_font
        else:
            return QVariant()

    def headerData(self, index, orientation, role):
        bold_font = QFont("Sans-serif", 9)
        bold_font.setBold(True)
        # Horizontal header
        if orientation == Qt.Horizontal:
            header = self.headers[index]
            if role == Qt.DisplayRole:
                return QVariant(header.capitalize())
            elif role == Qt.FontRole:
                if (
                    self._filters.get(header)
                    or self._state.sort_by == self.headers[index]
                ):
                    return bold_font
            elif role == Qt.SizeHintRole:
                # Set size hint for 'Name' column width (minimum width).
                if index == 0:
                    return QSize(200, 0)
        # Vertical indexing
        elif orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                return QVariant(str(index + 1))
            elif role == Qt.FontRole:
                if index == self.get_active_row():
                    return bold_font
        return QVariant()

    def sort(self, index: int, order=Qt.DescendingOrder):
        header = self.headers[index]
        if header not in ["time", "3bv/s"]:
            return
        self._state.sort_by = header
        self.filter_and_sort()
        self.sort_changed.emit(index)

    # -------------------------------------------------------------------------
    # New methods
    # -------------------------------------------------------------------------
    def update_highscores_group(
        self, settings: highscores.HighscoreSettingsStruct
    ) -> None:
        """
        Change the data to be highscores for a different set of settings.
        """
        self._all_data = highscores.get_highscores(settings=settings)
        self.filter_and_sort()

    def get_active_row(self) -> Optional[int]:
        """Get the index of the row containing the active highscore."""
        if self._state.current_highscore in self._displayed_data:
            return self._displayed_data.index(self._state.current_highscore)
        else:
            return None

    def format_data(self, row: int, key: str) -> str:
        """Get the string to display in a given cell."""
        h = self._displayed_data[row]
        if key == "time":
            return f"{h.elapsed + 0.005 : 6.2f}"
        elif key == "3bv":
            return f"{h.bbbv:3d}"
        elif key == "3bv/s":
            return f"{h.bbbvps + 0.005 : .2f}"
        elif key == "name":
            return h.name
        elif key == "date":
            return tm.strftime("%Y-%m-%d %H:%M:%S", tm.localtime(h.timestamp))
        elif key == "flagging":
            return "F" if utils.is_flagging_threshold(h.flagging) else "NF"
        else:
            return "<unhandled>"

    def filter_and_sort(self):
        """Update the displayed data based on current filters/sorting."""
        self.layoutAboutToBeChanged.emit()
        self._displayed_data = highscores.filter_and_sort(
            self._all_data, self._state.sort_by, self._filters
        )
        self.layoutChanged.emit()
        dummy_index = self.createIndex(0, 0)
        self.dataChanged.emit(dummy_index, dummy_index)


class HighscoresTable(QTableView):
    """A table view for highscores."""

    add_filter = pyqtSignal(str, str)

    def __init__(self, model: HighscoresModel, state_: state.HighscoreWindowState):
        super().__init__()
        self._state: state.HighscoreWindowState = state_
        self.setModel(model)
        self._header = self.horizontalHeader()
        self._index = self.verticalHeader()
        self.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        # self.setMinimumWidth(500)
        self.setMinimumHeight(300)
        self.setStyleSheet(
            """
            background: rgb(215,215,255);
            font:       normal 9pt Sans-serif;
            """
        )
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QAbstractItemView.NoSelection)
        self.setFocusPolicy(Qt.NoFocus)
        self.setCornerButtonEnabled(False)
        self.setSortingEnabled(True)
        # Fix width of all columns, let first column stretch to width.
        self._header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self._header.setSortIndicatorShown(True)
        self.set_sort_indicator()
        # Sort indicator is changed by clicking a header column, although in
        #  most cases this won't change the sorting, so the indicator needs to
        #  be changed back.
        self._header.sortIndicatorChanged.connect(self.set_sort_indicator)
        self._header.sectionClicked.connect(self.show_header_menu)
        # Set height of rows.
        self._index.setSectionResizeMode(QHeaderView.ResizeToContents)
        self._index.setSectionsClickable(False)
        self._filter_menu = QMenu(None)
        self._block_header_menu = False

    @property
    def _model(self) -> HighscoresModel:
        return self.model()

    def hideEvent(self, event: QHideEvent):
        self._filter_menu.close()

    def set_sort_indicator(self, *_):
        """Set the sort indicator to match the actual sorting."""
        self._header.setSortIndicator(
            self._model.headers.index(self._state.sort_by), Qt.DescendingOrder
        )

    @pyqtSlot(int)
    def show_header_menu(self, col):
        """Pop up a mini entry menu for filtering on a column."""
        key = self._model.headers[col]
        if key not in ["name", "flagging"] or self._block_header_menu:
            self._block_header_menu = False
            return
        self._filter_menu = QMenu(self.parent())
        self._filter_menu.aboutToHide.connect(self.check_mouse_on_header_menu_hide)

        def get_filter_cb(key, f):
            def cb():
                self.add_filter.emit(key, f)
                self._block_header_menu = False

            return cb

        if key == "flagging":
            group = QActionGroup(self)
            group.setExclusive(True)
            for filter_string in ["All", "F", "NF"]:
                action = QAction(filter_string, group, checkable=True)
                if filter_string == "All" and not self._state.flagging_filter:
                    action.setChecked(True)
                    filter_string = ""
                elif filter_string == self._state.flagging_filter:
                    action.setChecked(True)
                self._filter_menu.addAction(action)
                action.triggered.connect(get_filter_cb(key, filter_string))

        elif key == "name":
            # Make button for resetting filter (show all).
            all_action = QAction("All", checkable=True)
            if not self._model._filters["name"]:
                all_action.setChecked(True)
            all_action.triggered.connect(get_filter_cb(key, None))
            self._filter_menu.addAction(all_action)  # add to menu
            self._filter_menu.addSeparator()  # patch highlighting with mouse movement
            ## Make entry bar for name filter.
            # Create the entry bar with the existing filter as the text.
            if self._state.name_hint:
                # Name in entry bar, if any.
                text = self._state.name_hint
            else:
                # If no name in entry bar, name currently filtered by.
                text = self._state.name_filter
            entry = QLineEdit(text, self)
            entry.selectAll()  # select all the text
            # Set focus to the entry bar when the menu is opened.
            self._filter_menu.aboutToShow.connect(entry.setFocus)

            def set_name_filter():
                self.add_filter.emit(key, entry.text().strip())
                self._filter_menu.hide()
                self._block_header_menu = False

            entry.returnPressed.connect(set_name_filter)  # enter applies filter
            name_action = QWidgetAction(self._filter_menu)  # to contain QLineEdit
            name_action.setDefaultWidget(entry)  # set widget on QWidgetAction
            self._filter_menu.addAction(name_action)  # add to menu
        self._filter_menu.index = col
        # Display menu in appropriate position, below header in column 'col'
        headerPos = self.mapToGlobal(self._header.pos())
        posY = headerPos.y() + self._header.height()
        posX = headerPos.x() + self._header.sectionPosition(col)
        pos = QPoint(posX, posY)
        self._filter_menu.exec_(pos)  # modal dialog
        self.resizeRowsToContents()

    def check_mouse_on_header_menu_hide(self):
        header_pos = self.mapToGlobal(self._header.pos())
        x_min = header_pos.x() + sum(
            [self._header.sectionSize(i) for i in range(self._filter_menu.index)]
        )
        width = self._header.sectionSize(self._filter_menu.index)
        y_min = header_pos.y()
        height = self.mapToGlobal(self._index.pos()).y() - y_min
        if QRect(x_min, y_min, width, height).contains(QCursor.pos()):
            self._block_header_menu = True


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    settings = highscores.HighscoreSettingsStruct.get_default()
    win = HighscoresWindow(None, settings)
    win.show()
    sys.exit(app.exec_())
