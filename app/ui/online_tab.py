from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QSpinBox, QProgressBar, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from core import inpi_scraper
from core.models import Processo
from .resultado_table import ResultadoTable
from .detalhe_dialog import DetalheDialog


class OnlineWorker(QObject):
    finished = pyqtSignal(list, int)
    error = pyqtSignal(str)

    def __init__(self, nome, titular, numero, classe, pagina):
        super().__init__()
        self.nome = nome
        self.titular = titular
        self.numero = numero
        self.classe = classe
        self.pagina = pagina

    def run(self):
        try:
            processos, total = inpi_scraper.buscar_marcas(
                nome=self.nome,
                titular=self.titular,
                numero=self.numero,
                classe=self.classe,
                pagina=self.pagina,
            )
            self.finished.emit(processos, total)
        except Exception as e:
            self.error.emit(str(e))


class OnlineTab(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # Info banner
        info = QLabel(
            "Pesquisa direta no portal do INPI (busca.inpi.gov.br). "
            "Requer conexão com a internet."
        )
        info.setStyleSheet(
            "background: #e8f4fd; border: 1px solid #bee5eb; "
            "padding: 6px; border-radius: 4px; color: #0c5460;"
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        # Search filters
        group = QGroupBox("Parâmetros de Busca Online")
        grid = QGridLayout(group)
        grid.setSpacing(8)

        self.inp_nome = QLineEdit()
        self.inp_nome.setPlaceholderText("Nome ou parte do nome da marca")

        self.inp_titular = QLineEdit()
        self.inp_titular.setPlaceholderText("Nome do titular")

        self.inp_numero = QLineEdit()
        self.inp_numero.setPlaceholderText("Número do processo")

        self.inp_classe = QLineEdit()
        self.inp_classe.setPlaceholderText("Classe Nice (ex: 35)")

        self.spn_pagina = QSpinBox()
        self.spn_pagina.setMinimum(1)
        self.spn_pagina.setMaximum(999)
        self.spn_pagina.setValue(1)
        self.spn_pagina.setFixedWidth(80)

        grid.addWidget(QLabel("Nome:"), 0, 0)
        grid.addWidget(self.inp_nome, 0, 1)
        grid.addWidget(QLabel("Titular:"), 0, 2)
        grid.addWidget(self.inp_titular, 0, 3)

        grid.addWidget(QLabel("Nº Processo:"), 1, 0)
        grid.addWidget(self.inp_numero, 1, 1)
        grid.addWidget(QLabel("Classe:"), 1, 2)
        grid.addWidget(self.inp_classe, 1, 3)

        grid.addWidget(QLabel("Página:"), 2, 0)
        grid.addWidget(self.spn_pagina, 2, 1)

        btn_row = QHBoxLayout()
        self.btn_buscar = QPushButton("Buscar Online")
        self.btn_buscar.setFixedHeight(32)
        self.btn_buscar.clicked.connect(self._buscar)

        self.btn_prox = QPushButton("Próxima Página →")
        self.btn_prox.setFixedHeight(32)
        self.btn_prox.setEnabled(False)
        self.btn_prox.clicked.connect(self._proxima_pagina)

        self.lbl_total = QLabel("")
        self.lbl_total.setStyleSheet("color: #0066cc; font-weight: bold;")

        btn_row.addWidget(self.btn_buscar)
        btn_row.addWidget(self.btn_prox)
        btn_row.addStretch()
        btn_row.addWidget(self.lbl_total)
        grid.addLayout(btn_row, 3, 0, 1, 4)

        for inp in [self.inp_nome, self.inp_titular, self.inp_numero, self.inp_classe]:
            inp.returnPressed.connect(self._buscar)

        layout.addWidget(group)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)

        self.table = ResultadoTable()
        self.table.processo_selecionado.connect(self._ver_detalhe)
        layout.addWidget(self.table, stretch=1)

    def _buscar(self):
        nome = self.inp_nome.text().strip()
        titular = self.inp_titular.text().strip()
        numero = self.inp_numero.text().strip()
        classe = self.inp_classe.text().strip()

        if not any([nome, titular, numero, classe]):
            QMessageBox.warning(self, "Aviso", "Informe ao menos um parâmetro de busca.")
            return

        self._executar_busca(nome, titular, numero, classe, self.spn_pagina.value())

    def _proxima_pagina(self):
        self.spn_pagina.setValue(self.spn_pagina.value() + 1)
        self._buscar()

    def _executar_busca(self, nome, titular, numero, classe, pagina):
        self.btn_buscar.setEnabled(False)
        self.btn_prox.setEnabled(False)
        self.progress.setVisible(True)
        self.lbl_total.setText("Buscando...")
        self.status_message.emit("Buscando no INPI online...")

        self._thread = QThread()
        self._worker = OnlineWorker(nome, titular, numero, classe, pagina)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_resultado)
        self._worker.error.connect(self._on_erro)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _on_resultado(self, processos: list[Processo], total: int):
        self.btn_buscar.setEnabled(True)
        self.progress.setVisible(False)
        self.table.carregar(processos)
        n = len(processos)
        self.lbl_total.setText(f"{n} resultado(s) (total estimado: {total})")
        self.btn_prox.setEnabled(n > 0)
        self.status_message.emit(f"Busca online: {n} resultado(s)")

    def _on_erro(self, msg: str):
        self.btn_buscar.setEnabled(True)
        self.progress.setVisible(False)
        self.lbl_total.setText("Erro na busca")
        QMessageBox.critical(
            self, "Erro de Conexão",
            f"Não foi possível conectar ao INPI:\n\n{msg}\n\n"
            "Verifique sua conexão com a internet."
        )
        self.status_message.emit("Erro na busca online")

    def _ver_detalhe(self, processo: Processo):
        dlg = DetalheDialog(processo, self)
        dlg.exec()
