"""
Main Application Window for the AD Manager.
Provides sidebar navigation and content area for all management panels.
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QFrame, QStatusBar,
    QButtonGroup, QApplication, QSizePolicy, QSpacerItem,
    QMessageBox, QSplashScreen,
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont, QIcon, QPixmap, QColor, QPainter

from core.ad_connection import ADConnection, ADConfig
from ui.styles import COLORS, MAIN_STYLESHEET
from ui.login_dialog import LoginDialog
from ui.user_management import UserManagementPanel
from ui.group_management import GroupManagementPanel
from ui.computer_management import ComputerManagementPanel
from ui.policy_management import PolicyManagementPanel
from ui.ou_management import OUManagementPanel
from ui.reports_panel import ReportsPanel
from ui.audit_panel import AuditPanel


class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""

    def __init__(self):
        super().__init__()
        self.ad = ADConnection()
        self.current_panel = None
        self.nav_buttons = []

        self._setup_window()
        self._setup_ui()
        self._show_login()

    def _setup_window(self):
        """Configure the main window."""
        self.setWindowTitle("Active Directory Manager - Freebuff")
        self.setMinimumSize(1400, 800)
        self.resize(1600, 900)

        # Apply stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)

    def _setup_ui(self):
        """Set up the main UI layout."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = self._create_sidebar()
        main_layout.addWidget(self.sidebar)

        # Content area
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Header
        self.header = self._create_header()
        content_layout.addWidget(self.header)

        # Stacked widget for panels
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("ContentArea")
        content_layout.addWidget(self.content_stack, 1)

        main_layout.addWidget(content_area, 1)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['surface']};
                border-top: 1px solid {COLORS['border']};
                padding: 4px 16px;
                font-size: 12px;
            }}
        """)
        self.setStatusBar(self.status_bar)

        # Initialize panels (lazy loading)
        self.panels = {}
        self._panel_classes = {
            'dashboard': ReportsPanel,
            'users': UserManagementPanel,
            'groups': GroupManagementPanel,
            'computers': ComputerManagementPanel,
            'policies': PolicyManagementPanel,
            'ous': OUManagementPanel,
            'audit': AuditPanel,
        }

    def _create_sidebar(self) -> QWidget:
        """Create the sidebar navigation."""
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # App title
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(16, 20, 16, 4)

        app_title = QLabel("🔐 AD Manager")
        app_title.setObjectName("SidebarTitle")
        title_layout.addWidget(app_title)

        app_subtitle = QLabel("Active Directory Tools")
        app_subtitle.setObjectName("SidebarSubtitle")
        title_layout.addWidget(app_subtitle)

        layout.addWidget(title_container)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #333; max-height: 1px; margin: 8px 16px;")
        layout.addWidget(sep)

        # Navigation buttons
        nav_items = [
            ("📊", "Dashboard", "dashboard"),
            ("👥", "Users", "users"),
            ("🏷️", "Groups", "groups"),
            ("🖥️", "Computers", "computers"),
            ("📋", "Group Policy", "policies"),
            ("📁", "Organizational Units", "ous"),
            ("📜", "Audit Trail", "audit"),
        ]

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        for icon, label, key in nav_items:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setMinimumHeight(42)
            btn.clicked.connect(lambda checked, k=key: self._on_nav_click(k))
            self.nav_group.addButton(btn)
            self.nav_buttons.append((key, btn))
            layout.addWidget(btn)

        layout.addStretch()

        # Connection info
        self.connection_label = QLabel("⚪ Not Connected")
        self.connection_label.setObjectName("StatusDisconnected")
        layout.addWidget(self.connection_label)

        # Disconnect button
        self.disconnect_btn = QPushButton("🔌 Disconnect")
        self.disconnect_btn.setObjectName("SecondaryButton")
        self.disconnect_btn.setMinimumHeight(36)
        self.disconnect_btn.clicked.connect(self._on_disconnect)
        self.disconnect_btn.setVisible(False)
        layout.addWidget(self.disconnect_btn)

        # Connect button
        self.connect_btn = QPushButton("🔗 Connect to AD")
        self.connect_btn.setMinimumHeight(36)
        self.connect_btn.clicked.connect(self._show_login)
        layout.addWidget(self.connect_btn)

        # About
        about_layout = QHBoxLayout()
        about_layout.setContentsMargins(16, 8, 16, 16)
        about_label = QLabel("AD Manager v1.0")
        about_label.setStyleSheet(f"color: #666; font-size: 11px;")
        about_layout.addWidget(about_label)
        about_layout.addStretch()
        layout.addLayout(about_layout)

        return sidebar

    def _create_header(self) -> QWidget:
        """Create the header bar."""
        header = QWidget()
        header.setObjectName("Header")

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 12, 24, 12)

        self.page_title = QLabel("Dashboard")
        self.page_title.setObjectName("PageTitle")
        layout.addWidget(self.page_title)

        self.page_subtitle = QLabel("Overview of your Active Directory environment")
        self.page_subtitle.setObjectName("PageSubtitle")
        layout.addWidget(self.page_subtitle)

        layout.addStretch()

        # Quick action buttons in header
        self.create_user_btn = QPushButton("➕ Create User")
        self.create_user_btn.setMinimumHeight(36)
        self.create_user_btn.clicked.connect(self._on_create_user)
        self.create_user_btn.setVisible(False)
        layout.addWidget(self.create_user_btn)

        return header

    def _on_nav_click(self, key: str):
        """Handle navigation button click."""
        self._switch_panel(key)

    def _switch_panel(self, key: str):
        """Switch to a panel by key."""
        # Update header
        titles = {
            'dashboard': ('Dashboard', 'Overview of your Active Directory environment'),
            'users': ('User Management', 'Search, create, and manage user accounts'),
            'groups': ('Group Management', 'Create and manage security and distribution groups'),
            'computers': ('Computer Management', 'Manage workstations and computer accounts'),
            'policies': ('Group Policy Management', 'View and link Group Policy Objects'),
            'ous': ('Organizational Units', 'Manage OU structure'),
            'audit': ('Audit Trail', 'Who changed what, when — every AD change is recorded'),
        }

        title, subtitle = titles.get(key, ('', ''))
        self.page_title.setText(title)
        self.page_subtitle.setText(subtitle)

        # Show/hide create user button
        self.create_user_btn.setVisible(key == 'users')

        # Load panel if needed
        if key not in self.panels:
            panel_class = self._panel_classes.get(key)
            if panel_class:
                panel = panel_class(self.ad, self)
                panel.status_message.connect(self._on_status_message)
                self.panels[key] = panel
                self.content_stack.addWidget(panel)

        # Switch to panel
        if key in self.panels:
            self.content_stack.setCurrentWidget(self.panels[key])
            self.current_panel = self.panels[key]

            # Auto-refresh on switch
            if hasattr(self.current_panel, 'refresh'):
                QTimer.singleShot(50, self.current_panel.refresh)

    def _show_login(self):
        """Show the login dialog."""
        dialog = LoginDialog(self)
        dialog.connection_requested.connect(self._on_connect)
        dialog.exec()

    def _on_connect(self, config: ADConfig):
        """Handle connection request."""
        self.status_bar.showMessage("Connecting to Active Directory...")

        # Try to connect
        success, message = self.ad.connect(config)

        if success:
            # Update UI
            self.connection_label.setText(f"🟢 Connected: {config.domain or config.server}")
            self.connection_label.setObjectName("StatusConnected")
            self.connection_label.setStyleSheet(f"color: {COLORS['success']}; font-size: 12px; padding: 8px 16px;")
            self.disconnect_btn.setVisible(True)
            self.connect_btn.setVisible(False)

            # Enable nav buttons
            for key, btn in self.nav_buttons:
                btn.setEnabled(True)

            self.status_bar.showMessage(f"Connected to {config.domain or config.server}")

            # Switch to dashboard
            self._switch_panel('dashboard')

        else:
            self.status_bar.showMessage(f"Connection failed: {message}")
            QMessageBox.critical(self, "Connection Failed", message)

    def _on_disconnect(self):
        """Disconnect from AD."""
        self.ad.disconnect()

        # Update UI
        self.connection_label.setText("⚪ Not Connected")
        self.connection_label.setObjectName("StatusDisconnected")
        self.connection_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; padding: 8px 16px;")
        self.disconnect_btn.setVisible(False)
        self.connect_btn.setVisible(True)

        # Clear panels
        for key in list(self.panels.keys()):
            panel = self.panels.pop(key)
            self.content_stack.removeWidget(panel)
            panel.deleteLater()

        # Disable nav buttons
        for key, btn in self.nav_buttons:
            btn.setEnabled(False)

        self.status_bar.showMessage("Disconnected from Active Directory")

    def _on_create_user(self):
        """Create a new user from the header button."""
        if self.current_panel and hasattr(self.current_panel, 'create_user'):
            self.current_panel.create_user()

    def _on_status_message(self, message: str):
        """Handle status messages from panels."""
        self.status_bar.showMessage(message, 5000)

    def closeEvent(self, event):
        """Handle window close."""
        # Disconnect from AD
        if self.ad.is_connected:
            self.ad.disconnect()
        event.accept()
