"""
Group Policy Management panel for the AD Manager.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QFrame, QGroupBox, QTabWidget, QAbstractItemView,
    QMenu, QApplication, QComboBox, QTextEdit, QFormLayout,
    QDialog, QDialogButtonBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor

from core.ad_connection import ADConnection, ADGPOInfo, ADOUInfo
from ui.widgets import (
    SearchBar, DetailPanel, ResultMessageBox,
)
from ui.styles import COLORS
from utils.helpers import extract_cn_from_dn, format_ad_date


class PolicyManagementPanel(QWidget):
    """Panel for managing Group Policy Objects."""

    status_message = pyqtSignal(str)

    def __init__(self, ad: ADConnection, parent=None):
        super().__init__(parent)
        self.ad = ad
        self._current_gpos = []
        self._selected_gpo = None

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
            placeholder="Search GPOs by name...",
            fields=["displayName", "name"],
        )
        self.search_bar.search_triggered.connect(self._on_search)
        self.search_bar.clear_triggered.connect(self._on_clear_search)
        layout.addWidget(self.search_bar, 1)

        # Link GPO button
        self.link_btn = QPushButton("🔗 Link GPO to OU")
        self.link_btn.setMinimumHeight(36)
        self.link_btn.setMinimumWidth(160)
        self.link_btn.clicked.connect(self._on_link_gpo)
        layout.addWidget(self.link_btn)

        return toolbar

    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Display Name", "Name", "Description", "Version",
            "Created", "Modified", "Path"
        ])

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

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

        # GPO Info tab
        info_tab = QWidget()
        info_layout = QVBoxLayout(info_tab)
        info_layout.setContentsMargins(16, 16, 16, 16)

        info_title = QLabel("Group Policy Information")
        info_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        info_layout.addWidget(info_title)

        info_text = QLabel(
            "💡 Group Policy Objects (GPOs) are used to manage configuration "
            "settings for users and computers in an Active Directory domain.\n\n"
            "Common GPO tasks:\n"
            "• Link GPOs to Organizational Units (OUs)\n"
            "• Set password policies\n"
            "• Configure desktop settings\n"
            "• Deploy software\n"
            "• Configure security settings\n"
            "• Manage folder redirection"
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(f"color: {COLORS['text_secondary']}; line-height: 1.5;")
        info_layout.addWidget(info_text)
        info_layout.addStretch()
        tabs.addTab(info_tab, "ℹ️ About GPOs")

        # Actions tab
        actions_tab = QWidget()
        actions_layout = QVBoxLayout(actions_tab)
        actions_layout.setSpacing(12)
        actions_layout.setContentsMargins(16, 16, 16, 16)

        actions_title = QLabel("GPO Actions")
        actions_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        actions_layout.addWidget(actions_title)

        # Link to OU
        link_group = QGroupBox("Link GPO to OU")
        link_layout = QVBoxLayout(link_group)

        link_info = QLabel(
            "Select a GPO and an OU to link it to. This applies the policy "
            "to all users/computers in that OU."
        )
        link_info.setWordWrap(True)
        link_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        link_layout.addWidget(link_info)

        self.link_ou_btn = QPushButton("🔗 Link Selected GPO to OU...")
        self.link_ou_btn.setMinimumHeight(36)
        self.link_ou_btn.clicked.connect(self._on_link_gpo)
        link_layout.addWidget(self.link_ou_btn)

        actions_layout.addWidget(link_group)

        # View Linked OUs
        view_group = QGroupBox("View Linked OUs")
        view_layout = QVBoxLayout(view_group)
        self.view_linked_btn = QPushButton("📁 View OUs linked to Selected GPO")
        self.view_linked_btn.setMinimumHeight(36)
        self.view_linked_btn.clicked.connect(self._on_view_linked_ous)
        view_layout.addWidget(self.view_linked_btn)
        actions_layout.addWidget(view_group)

        # Copy
        copy_group = QGroupBox("Copy Information")
        copy_layout = QHBoxLayout(copy_group)
        copy_dn_btn = QPushButton("Copy DN")
        copy_dn_btn.clicked.connect(lambda: self._copy_to_clipboard("dn"))
        copy_layout.addWidget(copy_dn_btn)
        copy_path_btn = QPushButton("Copy File Path")
        copy_path_btn.clicked.connect(lambda: self._copy_to_clipboard("path"))
        copy_layout.addWidget(copy_path_btn)
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

        self.status_message.emit("Loading GPOs...")
        QTimer.singleShot(100, self._do_refresh)

    def _do_refresh(self):
        try:
            gpos = self.ad.get_all_gpos()
            self._current_gpos = gpos
            self._populate_table(gpos)
            self.status_message.emit(f"Found {len(gpos)} GPOs")
        except Exception as e:
            self.status_message.emit(f"Error loading GPOs: {str(e)}")

    def _populate_table(self, gpos: list):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for gpo in gpos:
            row = self.table.rowCount()
            self.table.insertRow(row)

            item = QTableWidgetItem(gpo.display_name or gpo.name)
            item.setData(Qt.ItemDataRole.UserRole, gpo)
            self.table.setItem(row, 0, item)
            self.table.setItem(row, 1, QTableWidgetItem(gpo.name))
            self.table.setItem(row, 2, QTableWidgetItem(gpo.description))
            self.table.setItem(row, 3, QTableWidgetItem(str(gpo.version)))
            self.table.setItem(row, 4, QTableWidgetItem(format_ad_date(gpo.when_created)))
            self.table.setItem(row, 5, QTableWidgetItem(format_ad_date(gpo.when_changed)))
            self.table.setItem(row, 6, QTableWidgetItem(gpo.gpc_file_system_path))

        self.table.setSortingEnabled(True)

    def _on_search(self, query: str, field: str):
        if not self.ad.is_connected:
            return

        if not query:
            self._do_refresh()
            return

        try:
            gpos = self.ad.search_gpos(f"*{query}*")
            self._current_gpos = gpos
            self._populate_table(gpos)
            self.status_message.emit(f"Found {len(gpos)} GPOs matching '{query}'")
        except Exception as e:
            self.status_message.emit(f"Search error: {str(e)}")

    def _on_clear_search(self):
        self._do_refresh()

    def _on_selection_changed(self):
        selected = self.table.selectedItems()
        if not selected:
            self._selected_gpo = None
            self.detail_panel.clear()
            return

        gpo = selected[0].data(Qt.ItemDataRole.UserRole)
        if gpo:
            self._selected_gpo = gpo
            self._show_gpo_details(gpo)

    def _show_gpo_details(self, gpo: ADGPOInfo):
        self.detail_panel.clear()
        self.detail_panel.add_field("Display Name", gpo.display_name or gpo.name, bold_value=True)
        self.detail_panel.add_separator()
        self.detail_panel.add_field("Name (GUID)", gpo.name)
        self.detail_panel.add_field("Description", gpo.description)
        self.detail_panel.add_field("Version", str(gpo.version))
        self.detail_panel.add_field("Flags", str(gpo.flags))
        self.detail_panel.add_separator()
        self.detail_panel.add_field("Distinguished Name", gpo.dn)
        self.detail_panel.add_field("File System Path", gpo.gpc_file_system_path)
        self.detail_panel.add_separator()
        self.detail_panel.add_field("Created", format_ad_date(gpo.when_created))
        self.detail_panel.add_field("Modified", format_ad_date(gpo.when_changed))

    def _on_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return

        gpo = item.data(Qt.ItemDataRole.UserRole)
        if not gpo:
            return

        menu = QMenu(self)
        menu.addAction("📋 View Details").triggered.connect(lambda: self._show_gpo_details(gpo))
        menu.addSeparator()
        menu.addAction("🔗 Link to OU...").triggered.connect(lambda: self._link_gpo_to_ou(gpo))
        menu.addAction("📁 View Linked OUs").triggered.connect(lambda: self._view_linked_ous_for(gpo))
        menu.addSeparator()
        menu.addAction("📋 Copy DN").triggered.connect(lambda: self._copy_to_clipboard("dn", gpo))
        menu.addAction("📋 Copy File Path").triggered.connect(lambda: self._copy_to_clipboard("path", gpo))

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _on_link_gpo(self):
        if not self._selected_gpo:
            ResultMessageBox.warning(self, "Warning", "Please select a GPO first.")
            return

        self._link_gpo_to_ou(self._selected_gpo)

    def _link_gpo_to_ou(self, gpo: ADGPOInfo):
        """Link a GPO to an OU."""
        ous = self.ad.get_all_ous()

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Link GPO '{gpo.display_name or gpo.name}' to OU")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)

        info = QLabel(f"Select an OU to link GPO:\n\n{gpo.display_name or gpo.name}")
        info.setWordWrap(True)
        layout.addWidget(info)

        form = QFormLayout()
        ou_combo = QComboBox()
        for ou in ous:
            ou_combo.addItem(f"{ou.name} ({ou.dn})", ou.dn)
        form.addRow("Target OU:", ou_combo)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Link GPO")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            target_ou = ou_combo.currentData()
            if target_ou:
                success, message = self.ad.link_gpo_to_ou(gpo.dn, target_ou)
                if success:
                    ResultMessageBox.success(self, "GPO Linked", message)
                    self.status_message.emit(message)
                else:
                    ResultMessageBox.error(self, "Error", message)

    def _on_view_linked_ous(self):
        if not self._selected_gpo:
            ResultMessageBox.warning(self, "Warning", "Please select a GPO first.")
            return

        self._view_linked_ous_for(self._selected_gpo)

    def _view_linked_ous_for(self, gpo: ADGPOInfo):
        """View OUs that a GPO is linked to."""
        # This is a best-effort lookup - parsing gPLink is complex
        ResultMessageBox.info(
            self, "GPO Link Information",
            f"GPO '{gpo.display_name or gpo.name}'\n\n"
            f"File Path: {gpo.gpc_file_system_path}\n\n"
            "To view all GPO links, use Group Policy Management Console (GPMC) "
            "or check the gPLink attribute on each OU."
        )

    def _copy_to_clipboard(self, field: str, gpo: ADGPOInfo = None):
        target = gpo or self._selected_gpo
        if not target:
            return

        if field == "dn":
            value = target.dn
        elif field == "path":
            value = target.gpc_file_system_path
        elif field == "name":
            value = target.display_name or target.name
        else:
            return

        if value:
            QApplication.clipboard().setText(value)
            self.status_message.emit(f"Copied: {value[:50]}")
