"""
Group Management panel for the AD Manager.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QFrame, QMessageBox, QGroupBox, QTabWidget,
    QAbstractItemView, QMenu, QApplication, QCheckBox, QLineEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor

from core.ad_connection import ADConnection, ADGroupInfo
from ui.widgets import (
    SearchBar, DetailPanel, ResultMessageBox, CreateGroupDialog,
)
from ui.styles import COLORS
from utils.helpers import extract_cn_from_dn, format_ad_date


class GroupManagementPanel(QWidget):
    """Panel for managing Active Directory groups."""

    status_message = pyqtSignal(str)

    def __init__(self, ad: ADConnection, parent=None):
        super().__init__(parent)
        self.ad = ad
        self._current_groups = []
        self._selected_group = None

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
            placeholder="Search groups...",
            fields=["sAMAccountName", "name", "mail"],
        )
        self.search_bar.search_triggered.connect(self._on_search)
        self.search_bar.clear_triggered.connect(self._on_clear_search)
        layout.addWidget(self.search_bar, 1)

        # Create group button
        self.create_btn = QPushButton("➕ Create Group")
        self.create_btn.setMinimumHeight(36)
        self.create_btn.setMinimumWidth(130)
        self.create_btn.clicked.connect(self.create_group)
        layout.addWidget(self.create_btn)

        return toolbar

    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels([
            "Name", "Description", "Scope", "Type",
            "Members", "Created", "Managed By"
        ])

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
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

        # Members tab
        members_tab = QWidget()
        members_layout = QVBoxLayout(members_tab)
        self.members_table = QTableWidget()
        self.members_table.setColumnCount(2)
        self.members_table.setHorizontalHeaderLabels(["Member Name", "Distinguished Name"])
        self.members_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.members_table.setAlternatingRowColors(True)
        self.members_table.verticalHeader().setVisible(False)
        self.members_table.setShowGrid(False)
        members_layout.addWidget(self.members_table)
        tabs.addTab(members_tab, "👥 Members")

        # Actions tab
        actions_tab = QWidget()
        actions_layout = QVBoxLayout(actions_tab)
        actions_layout.setSpacing(12)
        actions_layout.setContentsMargins(16, 16, 16, 16)

        actions_title = QLabel("Group Actions")
        actions_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        actions_layout.addWidget(actions_title)

        # Add member
        add_member_group = QGroupBox("Add Member")
        add_layout = QHBoxLayout(add_member_group)
        self.add_member_input = QLineEdit()
        self.add_member_input.setPlaceholderText("Enter username to add...")
        add_layout.addWidget(self.add_member_input, 1)
        self.add_member_btn = QPushButton("➕ Add")
        self.add_member_btn.setMinimumHeight(36)
        self.add_member_btn.clicked.connect(self._on_add_member)
        add_layout.addWidget(self.add_member_btn)
        actions_layout.addWidget(add_member_group)

        # Remove member
        remove_member_group = QGroupBox("Remove Member")
        remove_layout = QHBoxLayout(remove_member_group)
        self.remove_member_input = QLineEdit()
        self.remove_member_input.setPlaceholderText("Enter username to remove...")
        remove_layout.addWidget(self.remove_member_input, 1)
        self.remove_member_btn = QPushButton("➖ Remove")
        self.remove_member_btn.setMinimumHeight(36)
        self.remove_member_btn.setObjectName("DangerButton")
        self.remove_member_btn.clicked.connect(self._on_remove_member)
        remove_layout.addWidget(self.remove_member_btn)
        actions_layout.addWidget(remove_member_group)

        # Copy
        copy_group = QGroupBox("Copy Information")
        copy_layout = QHBoxLayout(copy_group)
        self.copy_dn_btn = QPushButton("Copy DN")
        self.copy_dn_btn.clicked.connect(lambda: self._copy_to_clipboard("dn"))
        copy_layout.addWidget(self.copy_dn_btn)

        self.copy_name_btn = QPushButton("Copy Name")
        self.copy_name_btn.clicked.connect(lambda: self._copy_to_clipboard("name"))
        copy_layout.addWidget(self.copy_name_btn)
        actions_layout.addWidget(copy_group)

        actions_layout.addStretch()
        tabs.addTab(actions_tab, "⚡ Actions")

        layout.addWidget(tabs, 1)

        return widget

    def refresh(self):
        """Refresh the group list."""
        if not self.ad.is_connected:
            return

        self.status_message.emit("Loading groups...")
        QTimer.singleShot(100, self._do_refresh)

    def _do_refresh(self):
        try:
            groups = self.ad.search_groups("*")
            self._current_groups = groups
            self._populate_table(groups)
            self.status_message.emit(f"Found {len(groups)} groups")
        except Exception as e:
            self.status_message.emit(f"Error: {str(e)}")

    def _populate_table(self, groups: list):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for group in groups:
            row = self.table.rowCount()
            self.table.insertRow(row)

            item = QTableWidgetItem(group.name)
            item.setData(Qt.ItemDataRole.UserRole, group)
            self.table.setItem(row, 0, item)
            self.table.setItem(row, 1, QTableWidgetItem(group.description))
            self.table.setItem(row, 2, QTableWidgetItem(group.group_scope))
            self.table.setItem(row, 3, QTableWidgetItem(group.group_type))
            self.table.setItem(row, 4, QTableWidgetItem(str(group.member_count)))
            self.table.setItem(row, 5, QTableWidgetItem(format_ad_date(group.when_created)))
            self.table.setItem(row, 6, QTableWidgetItem(extract_cn_from_dn(group.managed_by) if group.managed_by else ""))

        self.table.setSortingEnabled(True)

    def _on_search(self, query: str, field: str):
        if not self.ad.is_connected:
            return

        if not query:
            self._do_refresh()
            return

        try:
            groups = self.ad.search_groups(f"*{query}*", field)
            self._current_groups = groups
            self._populate_table(groups)
            self.status_message.emit(f"Found {len(groups)} groups matching '{query}'")
        except Exception as e:
            self.status_message.emit(f"Search error: {str(e)}")

    def _on_clear_search(self):
        self._do_refresh()

    def _on_selection_changed(self):
        selected = self.table.selectedItems()
        if not selected:
            self._selected_group = None
            self._clear_detail_panel()
            return

        group = selected[0].data(Qt.ItemDataRole.UserRole)
        if group:
            self._selected_group = group
            self._show_group_details(group)

    def _show_group_details(self, group: ADGroupInfo):
        self.detail_panel.clear()
        self.detail_panel.add_field("Group Name", group.name, bold_value=True)
        self.detail_panel.add_separator()
        self.detail_panel.add_field("SAM Account Name", group.sam_account_name)
        self.detail_panel.add_field("Description", group.description)
        self.detail_panel.add_field("Scope", group.group_scope)
        self.detail_panel.add_field("Type", group.group_type)
        self.detail_panel.add_field("Email", group.email)
        self.detail_panel.add_field("Distinguished Name", group.dn)
        self.detail_panel.add_separator()
        self.detail_panel.add_field("Member Count", str(group.member_count))
        self.detail_panel.add_field("Managed By", extract_cn_from_dn(group.managed_by) if group.managed_by else "")
        self.detail_panel.add_field("Created", format_ad_date(group.when_created))
        self.detail_panel.add_field("Modified", format_ad_date(group.when_changed))

        # Members
        self.members_table.setRowCount(0)
        for member_dn in group.members:
            row = self.members_table.rowCount()
            self.members_table.insertRow(row)
            self.members_table.setItem(row, 0, QTableWidgetItem(extract_cn_from_dn(member_dn)))
            self.members_table.setItem(row, 1, QTableWidgetItem(member_dn))

    def _clear_detail_panel(self):
        self.detail_panel.clear()
        self.members_table.setRowCount(0)

    def _on_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return

        group = item.data(Qt.ItemDataRole.UserRole)
        if not group:
            return

        menu = QMenu(self)
        menu.addAction("📋 View Details").triggered.connect(lambda: self._show_group_details(group))

        menu.addSeparator()

        add_action = menu.addAction("➕ Add Member...")
        add_action.triggered.connect(lambda: self._on_add_member_to(group))

        remove_action = menu.addAction("➖ Remove Member...")
        remove_action.triggered.connect(lambda: self._on_remove_member_from(group))

        menu.addSeparator()

        copy_action = menu.addAction("📋 Copy DN")
        copy_action.triggered.connect(lambda: self._copy_to_clipboard("dn", group))

        menu.addSeparator()

        delete_action = menu.addAction("🗑️ Delete Group")
        delete_action.triggered.connect(lambda: self._delete_group(group))

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def create_group(self):
        ous = self.ad.get_all_ous()
        dialog = CreateGroupDialog(ous, self)

        if dialog.exec() == CreateGroupDialog.DialogCode.Accepted:
            data = dialog.get_data()
            success, message = self.ad.create_group(
                ou_dn=data['ou_dn'],
                name=data['name'],
                description=data['description'],
                scope=data['scope'],
                group_type=data['group_type'],
            )

            if success:
                ResultMessageBox.success(self, "Group Created", message)
                self.status_message.emit(message)
                self._do_refresh()
            else:
                ResultMessageBox.error(self, "Error", message)

    def _on_add_member(self):
        if not self._selected_group:
            ResultMessageBox.warning(self, "Warning", "Please select a group first.")
            return

        username = self.add_member_input.text().strip()
        if not username:
            ResultMessageBox.warning(self, "Warning", "Please enter a username.")
            return

        success, message = self.ad.add_user_to_group(username, self._selected_group.sam_account_name)
        if success:
            ResultMessageBox.success(self, "Member Added", message)
            self.status_message.emit(message)
            self.add_member_input.clear()
            self._do_refresh()
        else:
            ResultMessageBox.error(self, "Error", message)

    def _on_add_member_to(self, group: ADGroupInfo):
        from PyQt6.QtWidgets import QInputDialog
        username, ok = QInputDialog.getText(
            self, "Add Member", f"Enter username to add to '{group.name}':"
        )
        if ok and username:
            success, message = self.ad.add_user_to_group(username, group.sam_account_name)
            if success:
                ResultMessageBox.success(self, "Member Added", message)
                self._do_refresh()
            else:
                ResultMessageBox.error(self, "Error", message)

    def _on_remove_member(self):
        if not self._selected_group:
            ResultMessageBox.warning(self, "Warning", "Please select a group first.")
            return

        username = self.remove_member_input.text().strip()
        if not username:
            ResultMessageBox.warning(self, "Warning", "Please enter a username.")
            return

        success, message = self.ad.remove_user_from_group(username, self._selected_group.sam_account_name)
        if success:
            ResultMessageBox.success(self, "Member Removed", message)
            self.status_message.emit(message)
            self.remove_member_input.clear()
            self._do_refresh()
        else:
            ResultMessageBox.error(self, "Error", message)

    def _on_remove_member_from(self, group: ADGroupInfo):
        from PyQt6.QtWidgets import QInputDialog
        username, ok = QInputDialog.getText(
            self, "Remove Member", f"Enter username to remove from '{group.name}':"
        )
        if ok and username:
            success, message = self.ad.remove_user_from_group(username, group.sam_account_name)
            if success:
                ResultMessageBox.success(self, "Member Removed", message)
                self._do_refresh()
            else:
                ResultMessageBox.error(self, "Error", message)

    def _delete_group(self, group: ADGroupInfo):
        reply = ResultMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to DELETE group '{group.name}'?"
        )
        if reply:
            success, message = self.ad.delete_group(group.sam_account_name)
            if success:
                ResultMessageBox.success(self, "Deleted", message)
                self._do_refresh()
            else:
                ResultMessageBox.error(self, "Error", message)

    def _copy_to_clipboard(self, field: str, group: ADGroupInfo = None):
        target = group or self._selected_group
        if not target:
            return
        value = target.dn if field == "dn" else target.name
        if value:
            QApplication.clipboard().setText(value)
            self.status_message.emit(f"Copied: {value[:50]}")
