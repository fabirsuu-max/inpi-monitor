from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMenu, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from core.models import Processo

COLUNAS = [
    ("numero",          "Processo"),
    ("marca_nome",      "Nome da Marca"),
    ("titular_principal","Titular"),
    ("classes_nice_str","Classes"),
    ("despacho_nome",   "Despacho"),
    ("marca_apresentacao","Apresentação"),
    ("data_deposito",   "Depósito"),
    ("data_concessao",  "Concessão"),
    ("data_vigencia",   "Vigência"),
]

# Color coding by despacho type
DESPACHO_CORES = {
    "concessão": QColor("#d4edda"),
    "deferido": QColor("#d4edda"),
    "indeferido": QColor("#f8d7da"),
    "arquivado": QColor("#fff3cd"),
    "oposição": QColor("#cce5ff"),
    "publicação": QColor("#e2e3e5"),
    "extinção": QColor("#f8d7da"),
    "caducidade": QColor("#f8d7da"),
}


class ResultadoTable(QTableWidget):
    processo_selecionado = pyqtSignal(object)  # emits Processo

    def __init__(self, parent=None):
        super().__init__(parent)
        self._processos: list[Processo] = []
        self._setup()

    def _setup(self):
        self.setColumnCount(len(COLUNAS))
        self.setHorizontalHeaderLabels([c[1] for c in COLUNAS])
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.doubleClicked.connect(self._on_double_click)

        header = self.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        font = QFont()
        font.setPointSize(9)
        self.setFont(font)
        self.verticalHeader().setDefaultSectionSize(22)

    def carregar(self, processos: list[Processo]):
        self._processos = processos
        self.setSortingEnabled(False)
        self.setRowCount(0)
        self.setRowCount(len(processos))

        for row, p in enumerate(processos):
            for col, (attr, _) in enumerate(COLUNAS):
                val = getattr(p, attr, "")
                item = QTableWidgetItem(str(val))
                item.setData(Qt.ItemDataRole.UserRole, p)
                self._colorir(item, p)
                self.setItem(row, col, item)

        self.setSortingEnabled(True)

    def _colorir(self, item: QTableWidgetItem, p: Processo):
        despacho = p.despacho_nome.lower()
        for chave, cor in DESPACHO_CORES.items():
            if chave in despacho:
                item.setBackground(cor)
                break

    def _on_double_click(self, index):
        p = self.item(index.row(), 0)
        if p:
            processo = p.data(Qt.ItemDataRole.UserRole)
            if processo:
                self.processo_selecionado.emit(processo)

    def _context_menu(self, pos):
        row = self.rowAt(pos.y())
        if row < 0:
            return
        item = self.item(row, 0)
        if not item:
            return
        processo = item.data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)
        act_copy_num = menu.addAction("Copiar número do processo")
        act_copy_nome = menu.addAction("Copiar nome da marca")
        act_copy_row = menu.addAction("Copiar linha completa")
        menu.addSeparator()
        act_detail = menu.addAction("Ver detalhes")

        action = menu.exec(self.viewport().mapToGlobal(pos))
        if action == act_copy_num:
            QApplication.clipboard().setText(processo.numero)
        elif action == act_copy_nome:
            QApplication.clipboard().setText(processo.marca_nome)
        elif action == act_copy_row:
            cols = [getattr(processo, attr, "") for attr, _ in COLUNAS]
            QApplication.clipboard().setText("\t".join(str(c) for c in cols))
        elif action == act_detail:
            self.processo_selecionado.emit(processo)

    def processos(self) -> list[Processo]:
        return self._processos
