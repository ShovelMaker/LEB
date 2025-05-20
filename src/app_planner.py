import sys
import os
import json
import sqlite3
import threading
import webbrowser
import requests
from PyQt5 import QtCore, QtGui, QtWidgets

# Path to your SQLite DB
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE_DIR, 'resources.db')

# Base URL for item icons
ICON_BASE_URL = 'https://cdn.maxroll.gg/leplanner/icons/'

# Mapping slots to Maxroll category keys
SLOT_CATEGORY_MAP = {
    'slot_helmet':   ['helmets'],
    'slot_amulet':   ['amulets'],
    'slot_weapon':   [
        'swords','daggers','axes','maces','scepters',
        'staves','polearms','bows','crossbows','wands'
    ],
    'slot_body':     ['body_armor'],
    'slot_offhand':  ['shields','quivers','catalysts'],
    'slot_ring1':    ['rings'],
    'slot_ring2':    ['rings'],
    'slot_belt':     ['belts'],
    'slot_gloves':   ['gloves'],
    'slot_boots':    ['boots'],
    'slot_relic':    ['relics'],
}

class DraggableLabel(QtWidgets.QLabel):
    def __init__(self, key, parent=None):
        super().__init__(parent)
        self.key = key
        self.setFixedSize(96, 96)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet('border:2px solid #555; background:#222;')

    def mouseDoubleClickEvent(self, e):
        dlg = ItemPickerDialog(self.key, self)
        if dlg.exec_() and dlg.selected:
            itm = dlg.selected
            icon = itm.get('icon')
            if icon:
                try:
                    data = requests.get(ICON_BASE_URL + icon + '.png').content
                    pix = QtGui.QPixmap()
                    pix.loadFromData(data)
                    self.setPixmap(pix.scaled(96, 96, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
                except Exception:
                    self.setText(itm.get('displayName', ''))
            else:
                self.setText(itm.get('displayName', ''))

class ItemPickerDialog(QtWidgets.QDialog):
    def __init__(self, slot_key, parent=None):
        super().__init__(parent)
        self.selected = None
        self.setWindowTitle('Select Item')
        self.setFixedSize(360, 480)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        self.setModal(True)
        if parent:
            pg = parent.geometry()
            self.move(pg.x()+20, pg.y()+20)

        layout = QtWidgets.QVBoxLayout(self)
        self.search = QtWidgets.QLineEdit()
        self.search.setPlaceholderText('Search…')
        layout.addWidget(self.search)
        self.listw = QtWidgets.QListWidget()
        layout.addWidget(self.listw, 1)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        # Load items from DB for this slot
        items = []
        conn = sqlite3.connect(DB_PATH)
        for cat in SLOT_CATEGORY_MAP.get(slot_key, []):
            r = conn.execute(
                "SELECT data FROM endpoints WHERE endpoint=?",
                (f'maxroll/items/{cat}',)
            ).fetchone()
            if r and r[0]:
                items += json.loads(r[0])
        conn.close()
        self.all = items
        self.update_list(items)
        self.search.textChanged.connect(self.on_search)
        self.listw.itemDoubleClicked.connect(self.on_pick)

    def update_list(self, arr):
        self.listw.clear()
        for it in arr:
            name = it.get('displayName') or it.get('BaseTypeName', '')
            wi = QtWidgets.QListWidgetItem(name)
            wi.setData(QtCore.Qt.UserRole, it)
            self.listw.addItem(wi)

    def on_search(self, t):
        ft = t.lower()
        filt = [i for i in self.all if ft in (i.get('displayName','') + i.get('BaseTypeName','')).lower()]
        self.update_list(filt)

    def on_pick(self, item):
        self.selected = item.data(QtCore.Qt.UserRole)
        self.accept()

class PlannerApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ShovelMaker LE Planner')
        self.resize(1280, 800)
        self.init_ui()
        self.load_endpoints()

    def init_ui(self):
        main = QtWidgets.QSplitter()
        self.setCentralWidget(main)

        # Left panel
        left = QtWidgets.QWidget()
        main.addWidget(left)
        lv = QtWidgets.QVBoxLayout(left)
        form = QtWidgets.QFormLayout()
        lv.addLayout(form)
        self.cb = QtWidgets.QComboBox()
        form.addRow('Data Source:', self.cb)
        btn = QtWidgets.QPushButton('🔄 Refresh')
        btn.clicked.connect(self.do_refresh)
        form.addRow(btn)
        lv.addStretch()
        self.log = QtWidgets.QPlainTextEdit()
        self.log.setReadOnly(True)
        lv.addWidget(self.log, 1)

        # Right tabs
        tabs = QtWidgets.QTabWidget()
        main.addWidget(tabs)
        main.setStretchFactor(1, 3)

        # Equipment tab
        eq = QtWidgets.QWidget()
        tabs.addTab(eq, 'Equipment')
        grid = QtWidgets.QGridLayout(eq)

        # Banner images (place your images under project root)
        ban_eq = QtWidgets.QLabel()
        ban_eq.setPixmap(QtGui.QPixmap(os.path.join(BASE_DIR, 'equipment_banner.png')))
        grid.addWidget(ban_eq, 0, 1, 1, 2, QtCore.Qt.AlignCenter)

        # Slot mappings: key, row, col
        mapping = [
            ('slot_helmet', 1,1), ('slot_amulet',1,2),
            ('slot_weapon',2,0), ('slot_body',2,1), ('slot_offhand',2,2),
            ('slot_ring1',3,0), ('slot_belt',3,1), ('slot_ring2',3,2),
            ('slot_gloves',4,0), ('slot_boots',4,1), ('slot_relic',4,2)
        ]
        self.slots = {}
        for key, r, c in mapping:
            w = DraggableLabel(key)
            grid.addWidget(w, r, c)
            self.slots[key] = w

        # Idols banner + grid
        ban_id = QtWidgets.QLabel()
        ban_id.setPixmap(QtGui.QPixmap(os.path.join(BASE_DIR, 'idols_banner.png')))
        grid.addWidget(ban_id, 0,3, QtCore.Qt.AlignCenter)
        idol_grid = QtWidgets.QGridLayout()
        for rr in range(4):
            for cc in range(4):
                l = QtWidgets.QLabel()
                l.setFixedSize(64,64)
                l.setStyleSheet('border:1px solid #555; background:#222;')
                idol_grid.addWidget(l, rr, cc)
        grid.addLayout(idol_grid, 1,3, 3,1)

        # Blessings banner + grid
        ban_bl = QtWidgets.QLabel()
        ban_bl.setPixmap(QtGui.QPixmap(os.path.join(BASE_DIR, 'blessings_banner.png')))
        grid.addWidget(ban_bl, 4,3, QtCore.Qt.AlignCenter)
        bless_grid = QtWidgets.QGridLayout()
        for i in range(8):
            l = QtWidgets.QLabel()
            l.setFixedSize(48,48)
            l.setStyleSheet('border:1px solid #555; background:#222;')
            bless_grid.addWidget(l, i//4, i%4)
        grid.addLayout(bless_grid, 5,3)

        # Other tabs stub
        for nm in ['Passives','Skills','Weaver','Settings','Save/Load']:
            tabs.addTab(QtWidgets.QWidget(), nm)

    def log_msg(self, t):
        self.log.appendPlainText(t)

    def load_endpoints(self):
        self.cb.clear()
        try:
            conn = sqlite3.connect(DB_PATH)
            for row in conn.execute('SELECT endpoint FROM endpoints'):
                self.cb.addItem(row[0])
            conn.close()
        except Exception as e:
            self.log_msg(f'✖ Endpoint load error: {e}')

    def do_refresh(self):
        def bg():
            self.log_msg('▶ Refreshing…')
            try:
                from crawler import refresh_all
                refresh_all()
                self.log_msg('✔ Done.')
                self.load_endpoints()
            except Exception as e:
                self.log_msg(f'✖ {e}')
        threading.Thread(target=bg, daemon=True).start()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = PlannerApp()
    win.show()
    sys.exit(app.exec_())
