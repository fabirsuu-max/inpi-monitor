from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QLineEdit, QPushButton, QGroupBox,
    QListWidget, QListWidgetItem, QComboBox,
    QTextEdit, QMessageBox, QDialog, QDialogButtonBox,
    QFormLayout, QCheckBox, QProgressBar, QGridLayout
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
                resultados = xml_parser.filtrar(self.processos, **marca.criterios)
                database.salvar_historico(marca.id, resultados)
                self.resultado.emit(marca.id, resultados)
            except Exception as e:
                self.error.emit(f"Erro ao verificar '{marca.label()}': {e}")
        self.finalizado.emit()


class AdicionarDialog(QDialog):
    def __init__(self, marca: MarcaMonitorada = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Monitoramento" if not marca else "Editar Monitoramento")
        self.setMinimumWidth(480)
        self._setup_ui(marca)

    def _setup_ui(self, marca):
        layout = QVBoxLayout(self)

        # Syntax hint banner
        hint = QLabel(
            "<b>Operadores:</b> "
            "use <b>OR</b> para alternativas dentro do campo "
            "<i>(ex: MRC OR NRC OR BRC)</i> &nbsp;·&nbsp; "
            "use <b>AND</b> para exigir múltiplos termos "
            "<i>(ex: TECH AND BR)</i><br>"
            "Campos diferentes são sempre combinados com <b>AND</b> entre si."
        )
        hint.setStyleSheet(
            "background:#e8f4fd; border:1px solid #bee5eb; "
            "padding:6px; border-radius:4px; color:#0c5460;"
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # Criteria group
        grp = QGroupBox("Critérios de Busca")
        grid = QGridLayout(grp)
        grid.setSpacing(8)

        self.inp_nome = QLineEdit()
        self.inp_nome.setPlaceholderText("Ex: MRC OR NRC OR BRC")

        self.inp_titular = QLineEdit()
        self.inp_titular.setPlaceholderText("Ex: EMPRESA LTDA  ou  LTDA OR SA")

        self.inp_numero = QLineEdit()
        self.inp_numero.setPlaceholderText("Ex: 912345678  ou  9123 OR 9124")

        self.inp_classe = QLineEdit()
        self.inp_classe.setPlaceholderText("Ex: 35 OR 42")

        self.inp_desp_cod = QLineEdit()
        self.inp_desp_cod.setPlaceholderText("Ex: IPAS009  ou  IPAS009 OR IPAS044")

        self.inp_desp_nome = QLineEdit()
        self.inp_desp_nome.setPlaceholderText("Ex: Registro concedido")

        self.inp_natureza = QLineEdit()
        self.inp_natureza.setPlaceholderText("Ex: De Produto OR De Serviço")

        self.inp_apresentacao = QLineEdit()
        self.inp_apresentacao.setPlaceholderText("Ex: Nominativa OR Mista")

        self.chk_regex = QCheckBox("Tratar campo Nome como expressão regular (regex)")

        grid.addWidget(QLabel("Nome da marca:"), 0, 0)
        grid.addWidget(self.inp_nome, 0, 1)
        grid.addWidget(QLabel("Titular:"), 1, 0)
        grid.addWidget(self.inp_titular, 1, 1)
        grid.addWidget(QLabel("Nº Processo:"), 2, 0)
        grid.addWidget(self.inp_numero, 2, 1)
        grid.addWidget(QLabel("Classe Nice:"), 3, 0)
        grid.addWidget(self.inp_classe, 3, 1)
        grid.addWidget(QLabel("Cód. Despacho:"), 4, 0)
        grid.addWidget(self.inp_desp_cod, 4, 1)
        grid.addWidget(QLabel("Nome Despacho:"), 5, 0)
        grid.addWidget(self.inp_desp_nome, 5, 1)
        grid.addWidget(QLabel("Natureza:"), 6, 0)
        grid.addWidget(self.inp_natureza, 6, 1)
        grid.addWidget(QLabel("Apresentação:"), 7, 0)
        grid.addWidget(self.inp_apresentacao, 7, 1)
        grid.addWidget(self.chk_regex, 8, 0, 1, 2)

        layout.addWidget(grp)

        # Metadata
        meta = QFormLayout()
        self.inp_obs = QLineEdit()
        self.inp_obs.setPlaceholderText("Nome ou descrição para identificar este monitoramento")
        self.chk_ativo = QCheckBox("Ativo")
        self.chk_ativo.setChecked(True)
        meta.addRow("Observação:", self.inp_obs)
        meta.addRow("", self.chk_ativo)
        layout.addLayout(meta)

        # Populate when editing
        if marca:
            c = marca.criterios
            self.inp_nome.setText(c.get("nome", ""))
            self.inp_titular.setText(c.get("titular", ""))
            self.inp_numero.setText(c.get("numero", ""))
            self.inp_classe.setText(c.get("classe_nice", ""))
            self.inp_desp_cod.setText(c.get("despacho_codigo", ""))
            self.inp_desp_nome.setText(c.get("despacho_nome", ""))
            self.inp_natureza.setText(c.get("natureza", ""))
            self.inp_apresentacao.setText(c.get("apresentacao", ""))
            self.chk_regex.setChecked(bool(c.get("use_regex", False)))
            self.inp_obs.setText(marca.observacao)
            self.chk_ativo.setChecked(marca.ativo)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._validar)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _get_criterios(self) -> dict:
        c = {}
        if v := self.inp_nome.text().strip():
            c["nome"] = v
        if v := self.inp_titular.text().strip():
            c["titular"] = v
        if v := self.inp_numero.text().strip():
            c["numero"] = v
        if v := self.inp_classe.text().strip():
            c["classe_nice"] = v
        if v := self.inp_desp_cod.text().strip():
            c["despacho_codigo"] = v
        if v := self.inp_desp_nome.text().strip():
            c["despacho_nome"] = v
        if v := self.inp_natureza.text().strip():
            c["natureza"] = v
        if v := self.inp_apresentacao.text().strip():
            c["apresentacao"] = v
        if self.chk_regex.isChecked():
            c["use_regex"] = True
        return c

    def _validar(self):
        c = self._get_criterios()
        # Remove use_regex for the "has criteria" check
        has = any(k != "use_regex" for k in c)
        if not has:
            QMessageBox.warning(self, "Aviso", "Preencha ao menos um critério de busca.")
            return
        self.accept()

    def get_marca(self) -> MarcaMonitorada:
        criterios = self._get_criterios()
        # Build a label from criteria for display
        partes = []
        for k, v in criterios.items():
            if k == "use_regex":
                continue
            partes.append(f"{k}:{v}")
        if criterios.get("use_regex"):
            partes.append("regex")
        termo = ", ".join(partes)

        return MarcaMonitorada(
            id=None,
            termo=termo,
            tipo_busca="combinada",
            criterios=criterios,
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
            item = QListWidgetItem(f"{status} {m.label()}")
            item.setData(Qt.ItemDataRole.UserRole, m.id)
            self.lista.addItem(item)

    def _on_selecionar(self, row: int):
        has = row >= 0
        self.btn_edit.setEnabled(has)
        self.btn_del.setEnabled(has)
        self.btn_verificar.setEnabled(has and bool(self._processos))

        if has and row < len(self._marcas):
            marca = self._marcas[row]
            self.lbl_resultado.setText(f"Resultados: {marca.label()}")
            processos = self._resultados.get(marca.id, [])
            self.table.carregar(processos)
            n = len(processos)
            if n:
                self.status_message.emit(f"{n} resultado(s) para '{marca.label()}'")
            else:
                self.status_message.emit(f"Clique em 'Verificar' para buscar '{marca.label()}'")

    def _adicionar(self):
        dlg = AdicionarDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            marca = dlg.get_marca()
            database.adicionar_monitorada(marca)
            self._carregar_lista()
            self.status_message.emit(f"Adicionado: {marca.label()}")

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
            f"Remover '{marca.label()}' do monitoramento?\nO histórico também será apagado.",
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
