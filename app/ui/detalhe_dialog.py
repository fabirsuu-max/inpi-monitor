from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QGroupBox, QGridLayout, QScrollArea, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.models import Processo


class DetalheDialog(QDialog):
    def __init__(self, processo: Processo, parent=None):
        super().__init__(parent)
        self.processo = processo
        self.setWindowTitle(f"Processo {processo.numero}")
        self.setMinimumSize(600, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10)

        # Header
        header = QLabel(self.processo.marca_nome or "(sem nome)")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        header.setFont(font)
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(header)

        # Processo info
        info_group = QGroupBox("Informações do Processo")
        info_grid = QGridLayout(info_group)
        campos = [
            ("Número:", self.processo.numero),
            ("Depósito:", self.processo.data_deposito),
            ("Concessão:", self.processo.data_concessao),
            ("Vigência:", self.processo.data_vigencia),
            ("Apresentação:", self.processo.marca_apresentacao),
            ("Natureza:", self.processo.marca_natureza),
        ]
        for i, (label, val) in enumerate(campos):
            row, col = divmod(i, 2)
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold;")
            info_grid.addWidget(lbl, row, col * 2)
            info_grid.addWidget(QLabel(val), row, col * 2 + 1)
        content_layout.addWidget(info_group)

        # Despacho
        desp_group = QGroupBox("Despacho")
        desp_layout = QVBoxLayout(desp_group)
        desp_layout.addWidget(QLabel(f"<b>Código:</b> {self.processo.despacho_codigo}"))
        desp_layout.addWidget(QLabel(f"<b>Nome:</b> {self.processo.despacho_nome}"))
        content_layout.addWidget(desp_group)

        # Titulares
        tit_group = QGroupBox("Titulares")
        tit_layout = QVBoxLayout(tit_group)
        for t in self.processo.titulares:
            txt = f"{t.nome}"
            if t.pais:
                txt += f" — {t.pais}"
                if t.uf:
                    txt += f"/{t.uf}"
            tit_layout.addWidget(QLabel(txt))
        if not self.processo.titulares:
            tit_layout.addWidget(QLabel("(nenhum)"))
        content_layout.addWidget(tit_group)

        # Classes Nice
        if self.processo.classes_nice:
            nice_group = QGroupBox("Classes Nice")
            nice_layout = QVBoxLayout(nice_group)
            for cn in self.processo.classes_nice:
                lbl_classe = QLabel(f"<b>Classe {cn.codigo}</b> — {cn.status}")
                nice_layout.addWidget(lbl_classe)
                if cn.especificacao:
                    espec = QLabel(cn.especificacao)
                    espec.setWordWrap(True)
                    espec.setStyleSheet("color: #555; margin-left: 12px;")
                    nice_layout.addWidget(espec)
            content_layout.addWidget(nice_group)

        # Procurador
        if self.processo.procurador:
            proc_group = QGroupBox("Procurador")
            proc_layout = QVBoxLayout(proc_group)
            proc_layout.addWidget(QLabel(self.processo.procurador))
            content_layout.addWidget(proc_group)

        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(self.accept)
        layout.addWidget(btn_fechar)
