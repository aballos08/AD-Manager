"""
User Management panel for the AD Manager.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QFrame, QMessageBox, QGroupBox, QFormLayout, QTabWidget,
    QAbstractItemView, QMenu, QApplication, QLineEdit, QCheckBox,
    QComboBox,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QColor

from core.ad_connection import ADConnection, ADUserInfo
from ui.widgets import (
    SearchBar, InfoCard, DetailPanel, StatusBadge,
    ResultMessageBox, PasswordInput, CreateUserDialog,
    CloneUserDialog, LoadingOverlay,
)
from ui.styles import COLORS
from utils.helpers import format_ad_date, extract_cn_from_dn


class UserManagementPanel(QWidget):
    """Panel for managing Active Directory users."""

    status_message = pyqtSignal(str)

    def __init__(self, ad: ADConnection, parent=None):
        super().__init__(parent)
        self.ad = ad
        self._current_users = []
        self._selected_user = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Main content splitter
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

        # Search bar
        self.search_bar = SearchBar(
            placeholder="Search users by name, username, email...",
            fields=["sAMAccountName", "displayName", "mail", "sn", "givenName", "department"],
        )
        self.search_bar.search_triggered.connect(self._on_search)
        self.search_bar.clear_triggered.connect(self._on_clear_search)
        layout.addWidget(self.search_bar, 1)

        # Quick filter checkboxes
        filter_layout = QVBoxLayout()
        self.enabled_only = QCheckBox("Enabled only")
        self.enabled_only.setChecked(False)
        self.enabled_only.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.enabled_only)

        self.locked_filter = QCheckBox("Locked only")
        self.locked_filter.setChecked(False)
        self.locked_filter.stateChanged.connect(self._on_filter_changed)
        filter_layout.addWidget(self.locked_filter)

        layout.addLayout(filter_layout)

        return toolbar

    def _create_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels([
            "Username", "Display Name", "Email", "Department",
            "Title", "Enabled", "Locked", "Last Logon"
        ])

        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)

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

        # Tabs for different views
        tabs = QTabWidget()

        # Details tab
        details_tab = QWidget()
        details_layout = QVBoxLayout(details_tab)
        self.detail_panel = DetailPanel()
        details_layout.addWidget(self.detail_panel)
        details_layout.addStretch()
        tabs.addTab(details_tab, "📋 Details")

        # Groups tab
        groups_tab = QWidget()
        groups_layout = QVBoxLayout(groups_tab)
        self.groups_table = QTableWidget()
        self.groups_table.setColumnCount(2)
        self.groups_table.setHorizontalHeaderLabels(["Group Name", "Distinguished Name"])
        self.groups_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.groups_table.setAlternatingRowColors(True)
        self.groups_table.verticalHeader().setVisible(False)
        self.groups_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.groups_table.setShowGrid(False)
        groups_layout.addWidget(self.groups_table)
        tabs.addTab(groups_tab, "👥 Groups")

        # Quick actions tab
        actions_tab = QWidget()
        actions_layout = QVBoxLayout(actions_tab)
        actions_layout.setSpacing(12)
        actions_layout.setContentsMargins(16, 16, 16, 16)

        actions_title = QLabel("Quick Actions")
        actions_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        actions_layout.addWidget(actions_title)

        # Reset password
        pwd_group = QGroupBox("Reset Password")
        pwd_layout = QVBoxLayout(pwd_group)
        self.reset_pwd_btn = QPushButton("🔑 Reset Password")
        self.reset_pwd_btn.setMinimumHeight(36)
        self.reset_pwd_btn.clicked.connect(self._on_reset_password)
        pwd_layout.addWidget(self.reset_pwd_btn)
        actions_layout.addWidget(pwd_group)

        # Lock/Unlock
        lock_group = QGroupBox("Account Status")
        lock_layout = QHBoxLayout(lock_group)
        self.unlock_btn = QPushButton("🔓 Unlock Account")
        self.unlock_btn.setMinimumHeight(36)
        self.unlock_btn.clicked.connect(self._on_unlock)
        lock_layout.addWidget(self.unlock_btn)

        self.disable_btn = QPushButton("🚫 Disable Account")
        self.disable_btn.setObjectName("DangerButton")
        self.disable_btn.setMinimumHeight(36)
        self.disable_btn.clicked.connect(self._on_disable)
        lock_layout.addWidget(self.disable_btn)

        self.enable_btn = QPushButton("✅ Enable Account")
        self.enable_btn.setObjectName("SuccessButton")
        self.enable_btn.setMinimumHeight(36)
        self.enable_btn.clicked.connect(self._on_enable)
        lock_layout.addWidget(self.enable_btn)

        actions_layout.addWidget(lock_group)

        # Copy info
        copy_group = QGroupBox("Copy Information")
        copy_layout = QVBoxLayout(copy_group)
        copy_btn_layout = QHBoxLayout()

        self.copy_dn_btn = QPushButton("Copy DN")
        self.copy_dn_btn.clicked.connect(lambda: self._copy_to_clipboard("dn"))
        copy_btn_layout.addWidget(self.copy_dn_btn)

        self.copy_email_btn = QPushButton("Copy Email")
        self.copy_email_btn.clicked.connect(lambda: self._copy_to_clipboard("email"))
        copy_btn_layout.addWidget(self.copy_email_btn)

        self.copy_username_btn = QPushButton("Copy Username")
        self.copy_username_btn.clicked.connect(lambda: self._copy_to_clipboard("sam"))
        copy_btn_layout.addWidget(self.copy_username_btn)

        copy_layout.addLayout(copy_btn_layout)
        actions_layout.addWidget(copy_group)

        actions_layout.addStretch()
        tabs.addTab(actions_tab, "⚡ Actions")

        layout.addWidget(tabs, 1)

        return widget

    def refresh(self):
        """Refresh the user list."""
        if not self.ad.is_connected:
            return

        self.status_message.emit("Loading users...")
        QTimer.singleShot(100, self._do_refresh)

    def _do_refresh(self):
        """Perform the actual refresh."""
        try:
            users = self.ad.search_users("*")
            self._current_users = users
            self._populate_table(users)
            self.status_message.emit(f"Found {len(users)} users")
        except Exception as e:
            self.status_message.emit(f"Error loading users: {str(e)}")
            ResultMessageBox.error(self, "Error", f"Failed to load users: {str(e)}")

    def _populate_table(self, users: list):
        """Populate the table with user data."""
        self.table.setSortingEnabled(False)
        self.table.setRowCount(0)

        for user in users:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Username
            item = QTableWidgetItem(user.sam_account_name)
            item.setData(Qt.ItemDataRole.UserRole, user)
            self.table.setItem(row, 0, item)

            # Display Name
            self.table.setItem(row, 1, QTableWidgetItem(user.display_name))

            # Email
            self.table.setItem(row, 2, QTableWidgetItem(user.email))

            # Department
            self.table.setItem(row, 3, QTableWidgetItem(user.department))

            # Title
            self.table.setItem(row, 4, QTableWidgetItem(user.title))

            # Enabled
            enabled_item = QTableWidgetItem()
            if user.enabled:
                enabled_item.setText("✅ Yes")
                enabled_item.setForeground(QColor(COLORS['success']))
            else:
                enabled_item.setText("❌ No")
                enabled_item.setForeground(QColor(COLORS['danger']))
            enabled_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, enabled_item)

            # Locked
            locked_item = QTableWidgetItem()
            if user.locked_out:
                locked_item.setText("🔒 Yes")
                locked_item.setForeground(QColor(COLORS['danger']))
            else:
                locked_item.setText("🔓 No")
                locked_item.setForeground(QColor(COLORS['success']))
            locked_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, locked_item)

            # Last Logon
            self.table.setItem(row, 7, QTableWidgetItem(format_ad_date(user.when_changed)))

        self.table.setSortingEnabled(True)

    def _on_search(self, query: str, field: str):
        """Handle search."""
        if not self.ad.is_connected:
            return

        if not query:
            self._do_refresh()
            return

        try:
            users = self.ad.search_users(f"*{query}*", field)
            self._current_users = users
            self._populate_table(users)
            self.status_message.emit(f"Found {len(users)} users matching '{query}'")
        except Exception as e:
            self.status_message.emit(f"Search error: {str(e)}")

    def _on_clear_search(self):
        """Clear search and reload all users."""
        self._do_refresh()

    def _on_filter_changed(self):
        """Handle filter checkbox changes."""
        if not self.ad.is_connected:
            return

        try:
            if self.locked_filter.isChecked():
                users = self.ad.get_locked_accounts()
            elif self.enabled_only.isChecked():
                users = self.ad.search_users("*", "sAMAccountName", enabled_only=True)
            else:
                users = self.ad.search_users("*")

            self._current_users = users
            self._populate_table(users)
        except Exception as e:
            self.status_message.emit(f"Filter error: {str(e)}")

    def _on_selection_changed(self):
        """Handle table selection change."""
        selected = self.table.selectedItems()
        if not selected:
            self._selected_user = None
            self._clear_detail_panel()
            return

        user = selected[0].data(Qt.ItemDataRole.UserRole)
        if user:
            self._selected_user = user
            self._show_user_details(user)

    def _show_user_details(self, user: ADUserInfo):
        """Show user details in the detail panel."""
        self.detail_panel.clear()

        # Status
        status_text = "Active" if user.enabled else "Disabled"
        if user.locked_out:
            status_text += " | LOCKED"

        self.detail_panel.add_field("Status", status_text, bold_value=True)
        self.detail_panel.add_separator()
        self.detail_panel.add_field("Username", user.sam_account_name)
        self.detail_panel.add_field("Display Name", user.display_name)
        self.detail_panel.add_field("First Name", user.given_name)
        self.detail_panel.add_field("Last Name", user.sn)
        self.detail_panel.add_field("Email", user.email)
        self.detail_panel.add_field("Distinguished Name", user.dn)
        self.detail_panel.add_separator()
        self.detail_panel.add_field("Department", user.department)
        self.detail_panel.add_field("Title", user.title)
        self.detail_panel.add_field("Office", user.office)
        self.detail_panel.add_field("Phone", user.telephone)
        self.detail_panel.add_field("Mobile", user.mobile)
        self.detail_panel.add_field("Manager", extract_cn_from_dn(user.manager) if user.manager else "")
        self.detail_panel.add_separator()
        self.detail_panel.add_field("Description", user.description)
        self.detail_panel.add_field("Created", format_ad_date(user.when_created))
        self.detail_panel.add_field("Modified", format_ad_date(user.when_changed))
        self.detail_panel.add_field("Logon Count", str(user.logon_count))
        self.detail_panel.add_field("Bad Password Count", str(user.bad_password_count))

        # Groups
        self.groups_table.setRowCount(0)
        for group_dn in user.member_of:
            row = self.groups_table.rowCount()
            self.groups_table.insertRow(row)
            self.groups_table.setItem(row, 0, QTableWidgetItem(extract_cn_from_dn(group_dn)))
            self.groups_table.setItem(row, 1, QTableWidgetItem(group_dn))

    def _clear_detail_panel(self):
        """Clear the detail panel."""
        self.detail_panel.clear()
        self.groups_table.setRowCount(0)

    def _on_context_menu(self, pos):
        """Show context menu on right-click."""
        item = self.table.itemAt(pos)
        if not item:
            return

        user = item.data(Qt.ItemDataRole.UserRole)
        if not user:
            return

        menu = QMenu(self)

        # View details
        view_action = menu.addAction("📋 View Details")
        view_action.triggered.connect(lambda: self._show_user_details(user))

        menu.addSeparator()

        # Reset password
        pwd_action = menu.addAction("🔑 Reset Password")
        pwd_action.triggered.connect(lambda: self._reset_password_for(user))

        # Unlock
        if user.locked_out:
            unlock_action = menu.addAction("🔓 Unlock Account")
            unlock_action.triggered.connect(lambda: self._unlock_user(user))

        menu.addSeparator()

        # Enable/Disable
        if user.enabled:
            disable_action = menu.addAction("🚫 Disable Account")
            disable_action.triggered.connect(lambda: self._disable_user(user))
        else:
            enable_action = menu.addAction("✅ Enable Account")
            enable_action.triggered.connect(lambda: self._enable_user(user))

        menu.addSeparator()

        # Clone
        clone_action = menu.addAction("👤 Clone User")
        clone_action.triggered.connect(lambda: self._clone_user(user))

        # Copy
        copy_dn_action = menu.addAction("📋 Copy DN")
        copy_dn_action.triggered.connect(lambda: self._copy_to_clipboard("dn", user))

        menu.addSeparator()

        # Delete
        delete_action = menu.addAction("🗑️ Delete User")
        delete_action.triggered.connect(lambda: self._delete_user(user))

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _on_reset_password(self):
        """Reset password for selected user."""
        if self._selected_user:
            self._reset_password_for(self._selected_user)

    def _reset_password_for(self, user: ADUserInfo):
        """Reset password for a specific user."""
        dialog = PasswordInput("Reset Password", user.sam_account_name, self)
        if dialog.exec() == PasswordInput.DialogCode.Accepted:
            password = dialog.get_password()
            success, message = self.ad.reset_password(
                user.sam_account_name,
                password,
                dialog.must_change_password(),
            )

            if success:
                ResultMessageBox.success(self, "Password Reset", message)
                self.status_message.emit(message)
            else:
                ResultMessageBox.error(self, "Error", message)
                self.status_message.emit(f"Failed: {message}")

    def _on_unlock(self):
        """Unlock selected user."""
        if self._selected_user:
            self._unlock_user(self._selected_user)

    def _unlock_user(self, user: ADUserInfo):
        """Unlock a specific user."""
        if not user.locked_out:
            ResultMessageBox.info(self, "Info", f"User '{user.sam_account_name}' is not locked.")
            return

        reply = ResultMessageBox.question(
            self, "Confirm Unlock",
            f"Are you sure you want to unlock '{user.sam_account_name}'?"
        )

        if reply:
            success, message = self.ad.unlock_user(user.sam_account_name)
            if success:
                ResultMessageBox.success(self, "Unlocked", message)
                self.status_message.emit(message)
                self._do_refresh()
            else:
                ResultMessageBox.error(self, "Error", message)

    def _on_enable(self):
        """Enable selected user."""
        if self._selected_user:
            self._enable_user(self._selected_user)

    def _enable_user(self, user: ADUserInfo):
        """Enable a specific user."""
        success, message = self.ad.enable_user(user.sam_account_name)
        if success:
            ResultMessageBox.success(self, "Enabled", message)
            self.status_message.emit(message)
            self._do_refresh()
        else:
            ResultMessageBox.error(self, "Error", message)

    def _on_disable(self):
        """Disable selected user."""
        if self._selected_user:
            self._disable_user(self._selected_user)

    def _disable_user(self, user: ADUserInfo):
        """Disable a specific user."""
        reply = ResultMessageBox.question(
            self, "Confirm Disable",
            f"Are you sure you want to disable '{user.sam_account_name}'?"
        )

        if reply:
            success, message = self.ad.disable_user(user.sam_account_name)
            if success:
                ResultMessageBox.success(self, "Disabled", message)
                self.status_message.emit(message)
                self._do_refresh()
            else:
                ResultMessageBox.error(self, "Error", message)

    def _on_clone_user(self):
        """Clone selected user."""
        if self._selected_user:
            self._clone_user(self._selected_user)

    def _clone_user(self, user: ADUserInfo):
        """Clone a user."""
        ous = self.ad.get_all_ous()
        dialog = CloneUserDialog(user, ous, self)

        if dialog.exec() == CloneUserDialog.DialogCode.Accepted:
            data = dialog.get_data()

            success, message = self.ad.clone_user(
                source_sam=user.sam_account_name,
                new_sam=data['new_sam'],
                new_first_name=data['new_first_name'],
                new_last_name=data['new_last_name'],
                new_password=data['new_password'],
                ou_dn=data['ou_dn'] or None,
                copy_group_membership=data['copy_groups'],
            )

            if success:
                ResultMessageBox.success(self, "User Cloned", message)
                self.status_message.emit(message)
                self._do_refresh()
            else:
                ResultMessageBox.error(self, "Error", message)

    def _delete_user(self, user: ADUserInfo):
        """Delete a user."""
        reply = ResultMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to DELETE '{user.sam_account_name}'?\n\n"
            f"This action cannot be undone!"
        )

        if reply:
            success, message = self.ad.delete_user(user.sam_account_name)
            if success:
                ResultMessageBox.success(self, "Deleted", message)
                self.status_message.emit(message)
                self._do_refresh()
            else:
                ResultMessageBox.error(self, "Error", message)

    def _copy_to_clipboard(self, field: str, user: ADUserInfo = None):
        """Copy user info to clipboard."""
        target = user or self._selected_user
        if not target:
            return

        value = ""
        if field == "dn":
            value = target.dn
        elif field == "email":
            value = target.email
        elif field == "sam":
            value = target.sam_account_name

        if value:
            QApplication.clipboard().setText(value)
            self.status_message.emit(f"Copied to clipboard: {value[:50]}...")

    def create_user(self):
        """Open create user dialog."""
        ous = self.ad.get_all_ous()
        dialog = CreateUserDialog(ous, self)

        if dialog.exec() == CreateUserDialog.DialogCode.Accepted:
            data = dialog.get_data()

            success, message = self.ad.create_user(
                ou_dn=data['ou_dn'],
                sam_account_name=data['sam_account_name'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                password=data['password'],
                email=data['email'],
                display_name=data['display_name'],
                department=data['department'],
                title=data['title'],
                description=data['description'],
                must_change_password=data['must_change_password'],
            )

            if success:
                ResultMessageBox.success(self, "User Created", message)
                self.status_message.emit(message)
                self._do_refresh()
            else:
                ResultMessageBox.error(self, "Error", message)
