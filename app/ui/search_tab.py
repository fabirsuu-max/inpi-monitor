import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QCheckBox, QComboBox,
    QFileDialog, QProgressBar, QStatusBar, QGroupBox, QSplitter,
    QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QFont
from core import xml_parser
from core.models import Processo
from .resultado_table import ResultadoTable
from .detalhe_dialog import DetalheDialog


class LoadWorker(QObject):
    finished = pyqtSignal(list)
    progress = pyqtSignal(int, int)
    error = pyqtSignal(str)

    def __init__(self, filepath: str):
        super().__init__()
        self.filepath = filepath

    def run(self):
        try:
            processos = xml_parser.parse_xml(self.filepath, self.progress.emit)
            self.finished.emit(processos)
        except Exception as e:
            self.error.emit(str(e))


class SearchTab(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._processos: list[Processo] = []
        self._filepath = ""
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(6)

        # File picker
        file_group = QGroupBox("Arquivo XML da RPI")
        file_layout = QHBoxLayout(file_group)
        self.lbl_arquivo = QLabel("Nenhum arquivo carregado")
        self.lbl_arquivo.setStyleSheet("color: #666;")
        self.btn_abrir = QPushButton("Abrir XML...")
        self.btn_abrir.setFixedWidth(120)
        self.btn_abrir.clicked.connect(self._abrir_arquivo)
        file_layout.addWidget(self.lbl_arquivo, stretch=1)
        file_layout.addWidget(self.btn_abrir)
        main_layout.addWidget(file_group)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)

        # Filters
        filter_group = QGroupBox("Filtros de Pesquisa")
        filter_grid = QGridLayout(filter_group)
        filter_grid.setSpacing(8)

        self.inp_nome = QLineEdit()
        self.inp_nome.setPlaceholderText("Nome da marca (parcial, case insensitive)")

        self.inp_titular = QLineEdit()
        self.inp_titular.setPlaceholderText("Nome do titular ou razão social")

        self.inp_classe = QLineEdit()
        self.inp_classe.setPlaceholderText("Ex: 35, 42, 09")

        self.inp_despacho = QLineEdit()
        self.inp_despacho.setPlaceholderText("Ex: Concessão, IPAS158, oposição")

        self.cmb_apresentacao = QComboBox()
        self.cmb_apresentacao.addItems(["(Todas)", "Nominativa", "Mista", "Figurativa", "Tridimensional"])

        self.cmb_natureza = QComboBox()
        self.cmb_natureza.addItems(["(Todas)", "Produtos e/ou Serviço", "Coletiva", "Certificação"])

        self.inp_numero = QLineEdit()
        self.inp_numero.setPlaceholderText("Número do processo")

        self.chk_regex = QCheckBox("Usar Regex")
        self.chk_regex.setToolTip("Ativa busca por expressão regular")

        filter_grid.addWidget(QLabel("Nome:"), 0, 0)
        filter_grid.addWidget(self.inp_nome, 0, 1)
        filter_grid.addWidget(QLabel("Titular:"), 0, 2)
        filter_grid.addWidget(self.inp_titular, 0, 3)

        filter_grid.addWidget(QLabel("Classe Nice:"), 1, 0)
        filter_grid.addWidget(self.inp_classe, 1, 1)
        filter_grid.addWidget(QLabel("Despacho:"), 1, 2)
        filter_grid.addWidget(self.inp_despacho, 1, 3)

        filter_grid.addWidget(QLabel("Apresentação:"), 2, 0)
        filter_grid.addWidget(self.cmb_apresentacao, 2, 1)
        filter_grid.addWidget(QLabel("Natureza:"), 2, 2)
        filter_grid.addWidget(self.cmb_natureza, 2, 3)

        filter_grid.addWidget(QLabel("Nº Processo:"), 3, 0)
        filter_grid.addWidget(self.inp_numero, 3, 1)
        filter_grid.addWidget(self.chk_regex, 3, 2)

        # Action buttons
        btn_layout = QHBoxLayout()
        self.btn_pesquisar = QPushButton("Pesquisar")
        self.btn_pesquisar.setFixedHeight(32)
        self.btn_pesquisar.setEnabled(False)
        self.btn_pesquisar.clicked.connect(self._pesquisar)
        self.btn_pesquisar.setDefault(True)

        self.btn_limpar = QPushButton("Limpar Filtros")
        self.btn_limpar.setFixedHeight(32)
        self.btn_limpar.clicked.connect(self._limpar_filtros)

        self.btn_todos = QPushButton("Mostrar Todos")
        self.btn_todos.setFixedHeight(32)
        self.btn_todos.setEnabled(False)
        self.btn_todos.clicked.connect(self._mostrar_todos)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("color: #0066cc; font-weight: bold;")

        btn_layout.addWidget(self.btn_pesquisar)
        btn_layout.addWidget(self.btn_limpar)
        btn_layout.addWidget(self.btn_todos)
        btn_layout.addStretch()
        btn_layout.addWidget(self.lbl_count)

        filter_grid.addLayout(btn_layout, 4, 0, 1, 4)

        # Enter key triggers search
        for inp in [self.inp_nome, self.inp_titular, self.inp_classe,
                    self.inp_despacho, self.inp_numero]:
            inp.returnPressed.connect(self._pesquisar)

        main_layout.addWidget(filter_group)

        # Results
        self.table = ResultadoTable()
        self.table.processo_selecionado.connect(self._ver_detalhe)
        main_layout.addWidget(self.table, stretch=1)

    def _abrir_arquivo(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir XML da RPI",
            os.path.expanduser("~"),
            "Arquivos XML (*.xml);;Todos os arquivos (*)"
        )
        if not path:
            return
        self._filepath = path
        self.lbl_arquivo.setText(os.path.basename(path))
        self.lbl_arquivo.setStyleSheet("color: #333;")
        self._carregar_xml(path)

    def carregar_arquivo_externo(self, path: str):
        """Called from main window to load a specific XML."""
        self._filepath = path
        self.lbl_arquivo.setText(os.path.basename(path))
        self.lbl_arquivo.setStyleSheet("color: #333;")
        self._carregar_xml(path)

    def _carregar_xml(self, path: str):
        self.btn_abrir.setEnabled(False)
        self.btn_pesquisar.setEnabled(False)
        self.btn_todos.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_count.setText("Carregando...")
        self.status_message.emit(f"Carregando {os.path.basename(path)}...")

        self._thread = QThread()
        self._worker = LoadWorker(path)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_loaded)
        self._worker.error.connect(self._on_load_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _on_progress(self, current: int, total: int):
        if total > 0:
            pct = int(current / total * 100)
            self.progress_bar.setValue(pct)
            self.progress_bar.setFormat(f"{current:,} / {total:,} ({pct}%)")

    def _on_loaded(self, processos: list[Processo]):
        self._processos = processos
        self.progress_bar.setVisible(False)
        self.btn_abrir.setEnabled(True)
        self.btn_pesquisar.setEnabled(True)
        self.btn_todos.setEnabled(True)
        n = len(processos)
        self.lbl_count.setText(f"{n:,} processos carregados")
        self.status_message.emit(f"Arquivo carregado: {n:,} processos")
        self.table.carregar(processos)

    def _on_load_error(self, msg: str):
        from PyQt6.QtWidgets import QMessageBox
        self.progress_bar.setVisible(False)
        self.btn_abrir.setEnabled(True)
        self.lbl_count.setText("Erro ao carregar")
        QMessageBox.critical(self, "Erro", f"Não foi possível carregar o arquivo:\n{msg}")

    def _pesquisar(self):
        if not self._processos:
            return

        nome = self.inp_nome.text().strip()
        titular = self.inp_titular.text().strip()
        classe = self.inp_classe.text().strip()
        despacho = self.inp_despacho.text().strip()
        numero = self.inp_numero.text().strip()
        apresentacao = self.cmb_apresentacao.currentText()
        natureza = self.cmb_natureza.currentText()
        use_regex = self.chk_regex.isChecked()

        kwargs = {
            "nome": nome,
            "titular": titular,
            "classe_nice": classe,
            "despacho_nome": despacho,
            "numero": numero,
            "use_regex": use_regex,
        }
        if apresentacao != "(Todas)":
            kwargs["apresentacao"] = apresentacao
        if natureza != "(Todas)":
            kwargs["natureza"] = natureza

        resultados = xml_parser.filtrar(self._processos, **kwargs)
        self.table.carregar(resultados)
        n = len(resultados)
        total = len(self._processos)
        self.lbl_count.setText(f"{n:,} resultado(s) de {total:,}")
        self.status_message.emit(f"Pesquisa concluída: {n:,} resultado(s)")

    def _limpar_filtros(self):
        self.inp_nome.clear()
        self.inp_titular.clear()
        self.inp_classe.clear()
        self.inp_despacho.clear()
        self.inp_numero.clear()
        self.cmb_apresentacao.setCurrentIndex(0)
        self.cmb_natureza.setCurrentIndex(0)
        self.chk_regex.setChecked(False)

    def _mostrar_todos(self):
        self._limpar_filtros()
        self.table.carregar(self._processos)
        n = len(self._processos)
        self.lbl_count.setText(f"{n:,} processos")

    def _ver_detalhe(self, processo: Processo):
        dlg = DetalheDialog(processo, self)
        dlg.exec()

    def get_processos(self) -> list[Processo]:
        return self._processos
