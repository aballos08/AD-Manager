"""
Organizational Unit (OU) Management panel for the AD Manager.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QFrame, QGroupBox, QTabWidget, QAbstractItemView,
    QMenu, QApplication, QFormLayout, QDialog,
    QDialogButtonBox, QLineEdit, QTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor

from core.ad_connection import ADConnection, ADOUInfo
from ui.widgets import (
    SearchBar, DetailPanel, ResultMessageBox,
)
from ui.styles import COLORS
from utils.helpers import format_ad_date, extract_cn_from_dn


class OUManagementPanel(QWidget):
    """Panel for managing Organizational Units."""

    status_message = pyqtSignal(str)

    def __init__(self, ad: ADConnection, parent=None):
        super().__init__(parent)
        self.ad = ad
        self._current_ous = []
        self._selected_ou = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Splitter
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Table
        self.table = self._create_table()
        splitter.addWidget(self.table)

        # Detail panel
        detail_widget = self._create_detail_panel()
        splitter.addWidget(detail_widget)

        splitter.setSizes([400, 300])
        layout.addWidget(splitter, 1)

    def _create_toolbar(self) -> QWidget:
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-bottom: 1px solid {COLORS['border']};
                padding: 8px 16px;
            }}
        """)
        toolbar.setFixedHeight(60)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(16, 8, 16, 8)

        self.search_bar = SearchBar(
            placeholder="Search OUs by name...",
            fields=["ou", "name"],
        )
        self.search_bar.search_triggered.connect(self._on_search)
        self.search_bar.clear_triggered.connect(self._on_clear_search)
        layout.addWidget(self.search_bar, 1)

        # Create OU button
        self.create_btn = QPushButton("➕ Create OU")
        self.create_btn.setMinimumHeight(36)
        self.create_btn.setMinimumWidth(120)
        self.create_btn.clicked.connect(self._on_create_ou)
        layout.addWidget(self.create_btn)

        return toolbar

    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "Name", "Description", "Distinguished Name", "Created", "Modified"
        ])

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)

        table.itemSelectionChanged.connect(self._on_selection_changed)
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(self._on_context_menu)

        return table

    def _create_detail_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()

        # Details tab
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        self.detail_panel = DetailPanel()
        details_layout.addWidget(self.detail_panel)
        details_layout.addStretch()
        tabs.addTab(details_tab, "📋 Details")

        # Actions tab
        actions_tab = QWidget()
        actions_layout = QVBoxLayout(actions_tab)
        actions_layout.setSpacing(12)
        actions_layout.setContentsMargins(16, 16, 16, 16)

        actions_title = QLabel("OU Actions")
        actions_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        actions_layout.addWidget(actions_title)

        # Move objects
        move_group = QGroupBox("Move Objects to this OU")
        move_layout = QVBoxLayout(move_group)
        move_info = QLabel(
            "To move users or computers to this OU, use the context menu "
            "on the user/computer in their respective management panels."
        )
        move_info.setWordWrap(True)
        move_info.setStyleSheet(f"color: {COLORS['text_secondary']};")
        move_layout.addWidget(move_info)
        actions_layout.addWidget(move_group)

        # Copy
        copy_group = QGroupBox("Copy Information")
        copy_layout = QHBoxLayout(copy_group)
        copy_dn_btn = QPushButton("Copy DN")
        copy_dn_btn.clicked.connect(lambda: self._copy_to_clipboard("dn"))
        copy_layout.addWidget(copy_dn_btn)
        copy_name_btn = QPushButton("Copy Name")
        copy_name_btn.clicked.connect(lambda: self._copy_to_clipboard("name"))
        copy_layout.addWidget(copy_name_btn)
        actions_layout.addWidget(copy_group)

        actions_layout.addStretch()
        tabs.addTab(actions_tab, "⚡ Actions")

        layout.addWidget(tabs, 1)

        return widget

    def refresh(self):
        if not self.ad.is_connected:
            return

        self.status_message.emit("Loading OUs...")
        QTimer.singleShot(100, self._do_refresh)

    def _do_refresh(self):
        try:
            ous = self.ad.get_all_ous()
            self._current_ous = ous
            self._populate_table(ous)
            self.status_message.emit(f"Found {len(ous)} OUs")
        except Exception as e:
            self.status_message.emit(f"Error: {str(e)}")

    def _populate_table(self, ous: list):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for ou in ous:
            row = self.table.rowCount()
            self.table.insertRow(row)

            item = QTableWidgetItem(ou.name)
            item.setData(Qt.ItemDataRole.UserRole, ou)
            self.table.setItem(row, 0, item)
            self.table.setItem(row, 1, QTableWidgetItem(ou.description))
            self.table.setItem(row, 2, QTableWidgetItem(ou.dn))
            self.table.setItem(row, 3, QTableWidgetItem(format_ad_date(ou.when_created)))
            self.table.setItem(row, 4, QTableWidgetItem(format_ad_date(ou.when_changed)))

        self.table.setSortingEnabled(True)

    def _on_search(self, query: str, field: str):
        if not self.ad.is_connected:
            return

        if not query:
            self._do_refresh()
            return

        # Filter locally since AD doesn't have many OUs
        filtered = [
            ou for ou in self._current_ous
            if query.lower() in ou.name.lower() or query.lower() in ou.description.lower()
        ]
        self._populate_table(filtered)
        self.status_message.emit(f"Found {len(filtered)} OUs matching '{query}'")

    def _on_clear_search(self):
        self._do_refresh()

    def _on_selection_changed(self):
        selected = self.table.selectedItems()
        if not selected:
            self._selected_ou = None
            self.detail_panel.clear()
            return

        ou = selected[0].data(Qt.ItemDataRole.UserRole)
        if ou:
            self._selected_ou = ou
            self._show_ou_details(ou)

    def _show_ou_details(self, ou: ADOUInfo):
        self.detail_panel.clear()
        self.detail_panel.add_field("OU Name", ou.name, bold_value=True)
        self.detail_panel.add_separator()
        self.detail_panel.add_field("Description", ou.description)
        self.detail_panel.add_field("Distinguished Name", ou.dn)
        self.detail_panel.add_separator()
        self.detail_panel.add_field("Created", format_ad_date(ou.when_created))
        self.detail_panel.add_field("Modified", format_ad_date(ou.when_changed))

    def _on_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return

        ou = item.data(Qt.ItemDataRole.UserRole)
        if not ou:
            return

        menu = QMenu(self)
        menu.addAction("📋 View Details").triggered.connect(lambda: self._show_ou_details(ou))
        menu.addSeparator()
        menu.addAction("📋 Copy DN").triggered.connect(lambda: self._copy_to_clipboard("dn", ou))
        menu.addAction("📋 Copy Name").triggered.connect(lambda: self._copy_to_clipboard("name", ou))

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _on_create_ou(self):
        """Create a new OU."""
        from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(
            self, "Create OU", "Enter OU name:"
        )
        if ok and name:
            # Find parent OU (domain root)
            base_dn = self.ad.config.base_dn if self.ad.config else ""

            reply = ResultMessageBox.question(
                self, "Create OU",
                f"Create OU '{name}' at the domain root?\n\nBase DN: {base_dn}"
            )

            if reply:
                success, msg = self.ad.create_ou(name, base_dn)
                if success:
                    ResultMessageBox.success(self, "OU Created", msg)
                    self._do_refresh()
                else:
                    ResultMessageBox.error(self, "Error", msg)

    def _copy_to_clipboard(self, field: str, ou: ADOUInfo = None):
        target = ou or self._selected_ou
        if not target:
            return
        value = target.dn if field == "dn" else target.name
        if value:
            QApplication.clipboard().setText(value)
            self.status_message.emit(f"Copied: {value}")
