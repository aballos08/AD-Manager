"""
Computer/Workstation Management panel for the AD Manager.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QFrame, QGroupBox, QTabWidget, QAbstractItemView,
    QMenu, QApplication, QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor

from core.ad_connection import ADConnection, ADComputerInfo
from ui.widgets import (
    SearchBar, DetailPanel, ResultMessageBox,
)
from ui.styles import COLORS
from utils.helpers import extract_cn_from_dn, format_ad_date


class ComputerManagementPanel(QWidget):
    """Panel for managing Active Directory computers/workstations."""

    status_message = pyqtSignal(str)

    def __init__(self, ad: ADConnection, parent=None):
        super().__init__(parent)
        self.ad = ad
        self._current_computers = []
        self._selected_computer = None

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
            placeholder="Search computers by name...",
            fields=["name", "sAMAccountName", "dnsHostName"],
        )
        self.search_bar.search_triggered.connect(self._on_search)
        self.search_bar.clear_triggered.connect(self._on_clear_search)
        layout.addWidget(self.search_bar, 1)

        # Filter
        self.enabled_only = QCheckBox("Enabled only")
        self.enabled_only.stateChanged.connect(self._on_filter_changed)
        layout.addWidget(self.enabled_only)

        self.disabled_only = QCheckBox("Disabled only")
        self.disabled_only.stateChanged.connect(self._on_filter_changed)
        layout.addWidget(self.disabled_only)

        return toolbar

    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Name", "DNS Hostname", "Operating System",
            "Description", "Enabled", "Location", "Created"
        ])

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
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

        # Actions tab
        actions_tab = QWidget()
        actions_layout = QVBoxLayout(actions_tab)
        actions_layout.setSpacing(12)
        actions_layout.setContentsMargins(16, 16, 16, 16)

        actions_title = QLabel("Workstation Actions")
        actions_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        actions_layout.addWidget(actions_title)

        # Status actions
        status_group = QGroupBox("Account Status")
        status_layout = QHBoxLayout(status_group)

        self.enable_btn = QPushButton("✅ Enable")
        self.enable_btn.setObjectName("SuccessButton")
        self.enable_btn.setMinimumHeight(36)
        self.enable_btn.clicked.connect(self._on_enable)
        status_layout.addWidget(self.enable_btn)

        self.disable_btn = QPushButton("🚫 Disable")
        self.disable_btn.setObjectName("DangerButton")
        self.disable_btn.setMinimumHeight(36)
        self.disable_btn.clicked.connect(self._on_disable)
        status_layout.addWidget(self.disable_btn)

        actions_layout.addWidget(status_group)

        # Password actions
        pwd_group = QGroupBox("Password / Trust")
        pwd_layout = QVBoxLayout(pwd_group)

        self.reset_pwd_btn = QPushButton("🔑 Reset Computer Account (Rejoin)")
        self.reset_pwd_btn.setMinimumHeight(36)
        self.reset_pwd_btn.clicked.connect(self._on_reset_password)
        pwd_layout.addWidget(self.reset_pwd_btn)

        info_label = QLabel(
            "💡 Resetting the computer account allows you to rejoin the "
            "computer to the domain without deleting it."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        pwd_layout.addWidget(info_label)

        actions_layout.addWidget(pwd_group)

        # Move actions
        move_group = QGroupBox("Move Computer")
        move_layout = QVBoxLayout(move_group)
        move_info = QLabel("Right-click a computer and select 'Move to OU' to relocate it.")
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
        copy_hostname_btn = QPushButton("Copy Hostname")
        copy_hostname_btn.clicked.connect(lambda: self._copy_to_clipboard("hostname"))
        copy_layout.addWidget(copy_hostname_btn)
        actions_layout.addWidget(copy_group)

        actions_layout.addStretch()
        tabs.addTab(actions_tab, "⚡ Actions")

        layout.addWidget(tabs, 1)

        return widget

    def refresh(self):
        if not self.ad.is_connected:
            return

        self.status_message.emit("Loading computers...")
        QTimer.singleShot(100, self._do_refresh)

    def _do_refresh(self):
        try:
            computers = self.ad.search_computers("*")
            self._current_computers = computers
            self._populate_table(computers)
            self.status_message.emit(f"Found {len(computers)} computers")
        except Exception as e:
            self.status_message.emit(f"Error: {str(e)}")

    def _populate_table(self, computers: list):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for computer in computers:
            row = self.table.rowCount()
            self.table.insertRow(row)

            item = QTableWidgetItem(computer.name)
            item.setData(Qt.ItemDataRole.UserRole, computer)
            self.table.setItem(row, 0, item)
            self.table.setItem(row, 1, QTableWidgetItem(computer.dns_host_name))
            self.table.setItem(row, 2, QTableWidgetItem(computer.operating_system))
            self.table.setItem(row, 3, QTableWidgetItem(computer.description))

            enabled_item = QTableWidgetItem()
            if computer.enabled:
                enabled_item.setText("✅ Yes")
                enabled_item.setForeground(QColor(COLORS['success']))
            else:
                enabled_item.setText("❌ No")
                enabled_item.setForeground(QColor(COLORS['danger']))
            enabled_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, enabled_item)

            self.table.setItem(row, 5, QTableWidgetItem(computer.location))
            self.table.setItem(row, 6, QTableWidgetItem(format_ad_date(computer.when_created)))

        self.table.setSortingEnabled(True)

    def _on_search(self, query: str, field: str):
        if not self.ad.is_connected:
            return

        if not query:
            self._do_refresh()
            return

        try:
            computers = self.ad.search_computers(f"*{query}*", field)
            self._current_computers = computers
            self._populate_table(computers)
            self.status_message.emit(f"Found {len(computers)} computers matching '{query}'")
        except Exception as e:
            self.status_message.emit(f"Search error: {str(e)}")

    def _on_clear_search(self):
        self._do_refresh()

    def _on_filter_changed(self):
        if not self.ad.is_connected:
            return

        try:
            if self.disabled_only.isChecked():
                computers = self.ad.get_disabled_computers()
            elif self.enabled_only.isChecked():
                computers = self.ad.search_computers("*", "name", enabled_only=True)
            else:
                computers = self.ad.search_computers("*")

            self._current_computers = computers
            self._populate_table(computers)
        except Exception as e:
            self.status_message.emit(f"Filter error: {str(e)}")

    def _on_selection_changed(self):
        selected = self.table.selectedItems()
        if not selected:
            self._selected_computer = None
            self.detail_panel.clear()
            return

        computer = selected[0].data(Qt.ItemDataRole.UserRole)
        if computer:
            self._selected_computer = computer
            self._show_computer_details(computer)

    def _show_computer_details(self, computer: ADComputerInfo):
        self.detail_panel.clear()

        status_text = "Active" if computer.enabled else "Disabled"
        self.detail_panel.add_field("Status", status_text, bold_value=True)
        self.detail_panel.add_separator()
        self.detail_panel.add_field("Name", computer.name)
        self.detail_panel.add_field("SAM Account Name", computer.sam_account_name)
        self.detail_panel.add_field("DNS Host Name", computer.dns_host_name)
        self.detail_panel.add_field("Operating System", computer.operating_system)
        self.detail_panel.add_field("Description", computer.description)
        self.detail_panel.add_field("Location", computer.location)
        self.detail_panel.add_field("Managed By", extract_cn_from_dn(computer.managed_by) if computer.managed_by else "")
        self.detail_panel.add_separator()
        self.detail_panel.add_field("Distinguished Name", computer.dn)
        self.detail_panel.add_field("Created", format_ad_date(computer.when_created))
        self.detail_panel.add_field("Modified", format_ad_date(computer.when_changed))

        # Show group memberships
        if computer.member_of:
            groups = ", ".join([extract_cn_from_dn(dn) for dn in computer.member_of[:5]])
            self.detail_panel.add_field("Member Of", groups)

    def _on_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return

        computer = item.data(Qt.ItemDataRole.UserRole)
        if not computer:
            return

        menu = QMenu(self)

        menu.addAction("📋 View Details").triggered.connect(lambda: self._show_computer_details(computer))
        menu.addSeparator()

        if computer.enabled:
            menu.addAction("🚫 Disable").triggered.connect(lambda: self._disable_computer(computer))
        else:
            menu.addAction("✅ Enable").triggered.connect(lambda: self._enable_computer(computer))

        menu.addSeparator()

        menu.addAction("🔑 Reset Account").triggered.connect(lambda: self._reset_computer(computer))
        menu.addAction("📁 Move to OU...").triggered.connect(lambda: self._move_computer(computer))
        menu.addAction("📋 Copy DN").triggered.connect(lambda: self._copy_to_clipboard("dn", computer))

        menu.addSeparator()

        menu.addAction("🗑️ Delete").triggered.connect(lambda: self._delete_computer(computer))

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _on_enable(self):
        if self._selected_computer:
            self._enable_computer(self._selected_computer)

    def _enable_computer(self, computer: ADComputerInfo):
        success, message = self.ad.enable_computer(computer.name)
        if success:
            ResultMessageBox.success(self, "Enabled", message)
            self._do_refresh()
        else:
            ResultMessageBox.error(self, "Error", message)

    def _on_disable(self):
        if self._selected_computer:
            self._disable_computer(self._selected_computer)

    def _disable_computer(self, computer: ADComputerInfo):
        reply = ResultMessageBox.question(
            self, "Confirm",
            f"Disable computer '{computer.name}'?"
        )
        if reply:
            success, message = self.ad.disable_computer(computer.name)
            if success:
                ResultMessageBox.success(self, "Disabled", message)
                self._do_refresh()
            else:
                ResultMessageBox.error(self, "Error", message)

    def _on_reset_password(self):
        if self._selected_computer:
            self._reset_computer(self._selected_computer)

    def _reset_computer(self, computer: ADComputerInfo):
        reply = ResultMessageBox.question(
            self, "Confirm Reset",
            f"Reset the trust account for '{computer.name}'?\n\n"
            "You will need to rejoin the computer to the domain."
        )
        if reply:
            success, message = self.ad.reset_computer_password(computer.name)
            if success:
                ResultMessageBox.success(self, "Reset", message)
            else:
                ResultMessageBox.error(self, "Error", message)

    def _move_computer(self, computer: ADComputerInfo):
        ous = self.ad.get_all_ous()
        from PyQt6.QtWidgets import QInputDialog, QComboBox as QCB
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QFormLayout

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Move '{computer.name}' to OU")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout(dialog)
        form = QFormLayout()

        ou_combo = QCB()
        for ou in ous:
            ou_combo.addItem(ou.name, ou.dn)
        form.addRow("Target OU:", ou_combo)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            target_ou = ou_combo.currentData()
            if target_ou:
                success, message = self.ad.move_computer(computer.name, target_ou)
                if success:
                    ResultMessageBox.success(self, "Moved", message)
                    self._do_refresh()
                else:
                    ResultMessageBox.error(self, "Error", message)

    def _delete_computer(self, computer: ADComputerInfo):
        reply = ResultMessageBox.question(
            self, "Confirm Delete",
            f"DELETE computer '{computer.name}'?\n\nThis cannot be undone!"
        )
        if reply:
            success, message = self.ad.delete_computer(computer.name)
            if success:
                ResultMessageBox.success(self, "Deleted", message)
                self._do_refresh()
            else:
                ResultMessageBox.error(self, "Error", message)

    def _copy_to_clipboard(self, field: str, computer: ADComputerInfo = None):
        target = computer or self._selected_computer
        if not target:
            return
        if field == "dn":
            value = target.dn
        elif field == "name":
            value = target.name
        elif field == "hostname":
            value = target.dns_host_name
        else:
            return

        if value:
            QApplication.clipboard().setText(value)
            self.status_message.emit(f"Copied: {value}")
