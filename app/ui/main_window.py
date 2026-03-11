import os
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QStatusBar, QWidget,
    QVBoxLayout, QLabel, QToolBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon, QFont
from .search_tab import SearchTab
from .online_tab import OnlineTab
from .monitor_tab import MonitorTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("INPI Monitor — Marcas")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self._setup_ui()
        self._setup_menu()
        self._apply_style()

    def _setup_ui(self):
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)

        self.tab_xml = SearchTab()
        self.tab_online = OnlineTab()
        self.tab_monitor = MonitorTab()

        self.tabs.addTab(self.tab_xml, "📂  Pesquisa RPI (XML)")
        self.tabs.addTab(self.tab_online, "🌐  Pesquisa Online")
        self.tabs.addTab(self.tab_monitor, "👁  Monitoramento")

        self.setCentralWidget(self.tabs)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.lbl_status = QLabel("Pronto")
        self.status.addPermanentWidget(self.lbl_status)

        # Connect status signals
        self.tab_xml.status_message.connect(self._set_status)
        self.tab_online.status_message.connect(self._set_status)
        self.tab_monitor.status_message.connect(self._set_status)

        # When XML is loaded on search tab, share processos with monitor tab
        self.tab_xml.table.modelo_atualizado = None
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _setup_menu(self):
        menubar = self.menuBar()

        # File menu
        menu_arquivo = menubar.addMenu("Arquivo")

        act_abrir = QAction("Abrir XML da RPI...", self)
        act_abrir.setShortcut("Ctrl+O")
        act_abrir.triggered.connect(self._abrir_xml)
        menu_arquivo.addAction(act_abrir)

        menu_arquivo.addSeparator()

        act_sair = QAction("Sair", self)
        act_sair.setShortcut("Ctrl+Q")
        act_sair.triggered.connect(self.close)
        menu_arquivo.addAction(act_sair)

        # Help menu
        menu_ajuda = menubar.addMenu("Ajuda")
        act_sobre = QAction("Sobre", self)
        act_sobre.triggered.connect(self._sobre)
        menu_ajuda.addAction(act_sobre)

    def _abrir_xml(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir XML da RPI",
            os.path.expanduser("~"),
            "Arquivos XML (*.xml);;Todos (*)"
        )
        if path:
            self.tabs.setCurrentIndex(0)
            self.tab_xml.carregar_arquivo_externo(path)

    def _on_tab_changed(self, index: int):
        # Sync processos from XML tab to Monitor tab
        if index == 2:
            processos = self.tab_xml.get_processos()
            self.tab_monitor.set_processos(processos)

    def _set_status(self, msg: str):
        self.lbl_status.setText(msg)

    def _sobre(self):
        QMessageBox.about(
            self,
            "Sobre — INPI Monitor",
            "<b>INPI Monitor</b><br><br>"
            "Ferramenta para pesquisa e monitoramento de marcas no INPI.<br><br>"
            "Fonte de dados: Revista da Propriedade Industrial (RPI)<br>"
            "Busca em XML local e portal online do INPI.<br><br>"
            "<i>Uso pessoal</i>"
        )

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QTabBar::tab {
                padding: 8px 16px;
                font-size: 10pt;
                background: #e0e0e0;
                border: 1px solid #bbb;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: white;
                font-weight: bold;
                color: #003399;
            }
            QTabBar::tab:hover {
                background: #d0d8f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 6px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            QPushButton {
                padding: 4px 12px;
                border: 1px solid #aaa;
                border-radius: 4px;
                background: #f0f0f0;
            }
            QPushButton:hover {
                background: #dce8ff;
                border-color: #669;
            }
            QPushButton:pressed {
                background: #c0d0f0;
            }
            QPushButton:disabled {
                color: #999;
            }
            QLineEdit, QComboBox, QSpinBox {
                padding: 4px 6px;
                border: 1px solid #bbb;
                border-radius: 4px;
                background: white;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #3366cc;
            }
            QTableWidget {
                gridline-color: #e0e0e0;
                background: white;
                alternate-background-color: #f8f9ff;
                selection-background-color: #cce0ff;
                selection-color: black;
            }
            QHeaderView::section {
                background: #e8eaf6;
                padding: 4px;
                border: 1px solid #ccc;
                font-weight: bold;
            }
            QStatusBar {
                background: #f0f0f0;
                border-top: 1px solid #ccc;
            }
        """)
