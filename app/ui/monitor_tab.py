from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QListWidget, QListWidgetItem, QComboBox,
    QTextEdit, QMessageBox, QDialog, QDialogButtonBox,
    QFormLayout, QCheckBox, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from core import database, xml_parser
from core.models import MarcaMonitorada, Processo
from .resultado_table import ResultadoTable
from .detalhe_dialog import DetalheDialog


class MonitorWorker(QObject):
    resultado = pyqtSignal(int, list)  # (marca_id, processos)
    finalizado = pyqtSignal()
    progresso = pyqtSignal(int, int)
    error = pyqtSignal(str)

    def __init__(self, marcas: list[MarcaMonitorada], processos: list[Processo]):
        super().__init__()
        self.marcas = marcas
        self.processos = processos

    def run(self):
        total = len(self.marcas)
        for i, marca in enumerate(self.marcas):
            self.progresso.emit(i + 1, total)
            try:
                kwargs = {"use_regex": marca.tipo_busca == "regex"}
                if marca.tipo_busca in ("nome", "regex"):
                    kwargs["nome"] = marca.termo
                elif marca.tipo_busca == "titular":
                    kwargs["titular"] = marca.termo

                resultados = xml_parser.filtrar(self.processos, **kwargs)
                database.salvar_historico(marca.id, resultados)
                self.resultado.emit(marca.id, resultados)
            except Exception as e:
                self.error.emit(f"Erro ao verificar '{marca.termo}': {e}")
        self.finalizado.emit()


class AdicionarDialog(QDialog):
    def __init__(self, marca: MarcaMonitorada = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Monitoramento" if not marca else "Editar Monitoramento")
        self.setMinimumWidth(400)
        self._setup_ui(marca)

    def _setup_ui(self, marca):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.inp_termo = QLineEdit()
        self.inp_termo.setPlaceholderText("Termo a monitorar")

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["nome", "titular", "regex"])

        self.inp_obs = QLineEdit()
        self.inp_obs.setPlaceholderText("Observação opcional")

        self.chk_ativo = QCheckBox("Ativo")
        self.chk_ativo.setChecked(True)

        form.addRow("Termo:", self.inp_termo)
        form.addRow("Tipo de busca:", self.cmb_tipo)
        form.addRow("Observação:", self.inp_obs)
        form.addRow("", self.chk_ativo)

        if marca:
            self.inp_termo.setText(marca.termo)
            self.cmb_tipo.setCurrentText(marca.tipo_busca)
            self.inp_obs.setText(marca.observacao)
            self.chk_ativo.setChecked(marca.ativo)

        layout.addLayout(form)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validar)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _validar(self):
        if not self.inp_termo.text().strip():
            QMessageBox.warning(self, "Aviso", "Informe o termo a monitorar.")
            return
        self.accept()

    def get_marca(self) -> MarcaMonitorada:
        return MarcaMonitorada(
            id=None,
            termo=self.inp_termo.text().strip(),
            tipo_busca=self.cmb_tipo.currentText(),
            observacao=self.inp_obs.text().strip(),
            ativo=self.chk_ativo.isChecked(),
        )


class MonitorTab(QWidget):
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._processos: list[Processo] = []
        self._marcas: list[MarcaMonitorada] = []
        self._resultados: dict[int, list[Processo]] = {}
        database.init_db()
        self._setup_ui()
        self._carregar_lista()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: list of monitored brands
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel("Marcas Monitoradas")
        lbl.setStyleSheet("font-weight: bold; font-size: 11pt;")
        left_layout.addWidget(lbl)

        self.lista = QListWidget()
        self.lista.setMinimumWidth(220)
        self.lista.currentRowChanged.connect(self._on_selecionar)
        left_layout.addWidget(self.lista, stretch=1)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("+ Adicionar")
        self.btn_edit = QPushButton("Editar")
        self.btn_del = QPushButton("Remover")
        self.btn_edit.setEnabled(False)
        self.btn_del.setEnabled(False)
        self.btn_add.clicked.connect(self._adicionar)
        self.btn_edit.clicked.connect(self._editar)
        self.btn_del.clicked.connect(self._remover)
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_del)
        left_layout.addLayout(btn_row)

        splitter.addWidget(left)

        # Right panel: results
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        top_row = QHBoxLayout()
        self.lbl_resultado = QLabel("Selecione uma marca para ver resultados")
        self.lbl_resultado.setStyleSheet("font-weight: bold;")

        self.btn_verificar = QPushButton("Verificar Selecionada")
        self.btn_verificar.setEnabled(False)
        self.btn_verificar.clicked.connect(self._verificar_selecionada)

        self.btn_verificar_todas = QPushButton("Verificar Todas")
        self.btn_verificar_todas.clicked.connect(self._verificar_todas)

        top_row.addWidget(self.lbl_resultado, stretch=1)
        top_row.addWidget(self.btn_verificar)
        top_row.addWidget(self.btn_verificar_todas)
        right_layout.addLayout(top_row)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        right_layout.addWidget(self.progress)

        self.lbl_xml_aviso = QLabel(
            "Nenhum XML carregado. Abra um arquivo XML na aba 'Pesquisa RPI' primeiro."
        )
        self.lbl_xml_aviso.setStyleSheet(
            "background: #fff3cd; border: 1px solid #ffc107; "
            "padding: 6px; border-radius: 4px; color: #856404;"
        )
        self.lbl_xml_aviso.setVisible(True)
        right_layout.addWidget(self.lbl_xml_aviso)

        self.table = ResultadoTable()
        self.table.processo_selecionado.connect(self._ver_detalhe)
        right_layout.addWidget(self.table, stretch=1)

        splitter.addWidget(right)
        splitter.setSizes([250, 700])
        layout.addWidget(splitter, stretch=1)

    def set_processos(self, processos: list[Processo]):
        self._processos = processos
        self.lbl_xml_aviso.setVisible(len(processos) == 0)

    def _carregar_lista(self):
        self._marcas = database.listar_monitoradas()
        self.lista.clear()
        for m in self._marcas:
            status = "✓" if m.ativo else "✗"
            item = QListWidgetItem(f"{status} [{m.tipo_busca}] {m.termo}")
            item.setData(Qt.ItemDataRole.UserRole, m.id)
            self.lista.addItem(item)

    def _on_selecionar(self, row: int):
        has = row >= 0
        self.btn_edit.setEnabled(has)
        self.btn_del.setEnabled(has)
        self.btn_verificar.setEnabled(has and bool(self._processos))

        if has and row < len(self._marcas):
            marca = self._marcas[row]
            self.lbl_resultado.setText(f"Resultados: {marca.termo} [{marca.tipo_busca}]")
            processos = self._resultados.get(marca.id, [])
            self.table.carregar(processos)
            n = len(processos)
            if n:
                self.status_message.emit(f"{n} resultado(s) para '{marca.termo}'")
            else:
                self.status_message.emit(f"Clique em 'Verificar' para buscar '{marca.termo}'")

    def _adicionar(self):
        dlg = AdicionarDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            marca = dlg.get_marca()
            new_id = database.adicionar_monitorada(marca)
            self._carregar_lista()
            self.status_message.emit(f"Adicionado: {marca.termo}")

    def _editar(self):
        row = self.lista.currentRow()
        if row < 0 or row >= len(self._marcas):
            return
        marca = self._marcas[row]
        dlg = AdicionarDialog(marca, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            updated = dlg.get_marca()
            updated.id = marca.id
            database.atualizar_monitorada(updated)
            self._carregar_lista()

    def _remover(self):
        row = self.lista.currentRow()
        if row < 0 or row >= len(self._marcas):
            return
        marca = self._marcas[row]
        resp = QMessageBox.question(
            self, "Confirmar",
            f"Remover '{marca.termo}' do monitoramento?\nO histórico também será apagado.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            database.remover_monitorada(marca.id)
            self._resultados.pop(marca.id, None)
            self._carregar_lista()
            self.table.carregar([])
            self.lbl_resultado.setText("Selecione uma marca para ver resultados")

    def _verificar_selecionada(self):
        row = self.lista.currentRow()
        if row < 0 or row >= len(self._marcas):
            return
        marca = self._marcas[row]
        self._iniciar_verificacao([marca])

    def _verificar_todas(self):
        if not self._processos:
            QMessageBox.warning(
                self, "Aviso",
                "Carregue um arquivo XML na aba 'Pesquisa RPI' primeiro."
            )
            return
        ativas = [m for m in self._marcas if m.ativo]
        if not ativas:
            QMessageBox.information(self, "Aviso", "Nenhuma marca ativa para verificar.")
            return
        self._iniciar_verificacao(ativas)

    def _iniciar_verificacao(self, marcas: list[MarcaMonitorada]):
        self.btn_verificar.setEnabled(False)
        self.btn_verificar_todas.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(marcas))
        self.progress.setValue(0)
        self.status_message.emit(f"Verificando {len(marcas)} marca(s)...")

        self._thread = QThread()
        self._worker = MonitorWorker(marcas, self._processos)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.resultado.connect(self._on_resultado_parcial)
        self._worker.progresso.connect(lambda c, t: self.progress.setValue(c))
        self._worker.finalizado.connect(self._on_verificacao_completa)
        self._worker.error.connect(lambda e: self.status_message.emit(e))
        self._worker.finalizado.connect(self._thread.quit)
        self._thread.start()

    def _on_resultado_parcial(self, marca_id: int, processos: list[Processo]):
        self._resultados[marca_id] = processos
        row = self.lista.currentRow()
        if row >= 0 and row < len(self._marcas):
            if self._marcas[row].id == marca_id:
                self.table.carregar(processos)

    def _on_verificacao_completa(self):
        self.btn_verificar.setEnabled(bool(self._processos) and self.lista.currentRow() >= 0)
        self.btn_verificar_todas.setEnabled(True)
        self.progress.setVisible(False)
        total = sum(len(v) for v in self._resultados.values())
        self.status_message.emit(f"Verificação concluída. {total} resultado(s) encontrado(s).")

    def _ver_detalhe(self, processo: Processo):
        dlg = DetalheDialog(processo, self)
        dlg.exec()
