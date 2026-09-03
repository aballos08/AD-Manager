"""
Login/Connection dialog for Active Directory.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QGroupBox, QFormLayout, QComboBox,
    QMessageBox, QFrame, QSpacerItem, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QSettings
from PyQt6.QtGui import QFont

from core.ad_connection import ADConfig
from ui.styles import COLORS


class LoginDialog(QDialog):
    """Dialog for connecting to Active Directory."""

    connection_requested = pyqtSignal(ADConfig)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect to Active Directory")
        self.setMinimumWidth(520)
        self.setMinimumHeight(520)
        self.setModal(True)

        # Settings for remembering connection
        self.settings = QSettings("ADManager", "Connection")

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 32, 32, 32)

        # Title
        title = QLabel("🔐 Active Directory Connection")
        title.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {COLORS['text_primary']};
            margin-bottom: 4px;
        """)
        layout.addWidget(title)

        subtitle = QLabel("Enter your Active Directory server details to connect.")
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; margin-bottom: 12px;")
        layout.addWidget(subtitle)

        # Server settings group
        server_group = QGroupBox("Server Settings")
        server_layout = QFormLayout(server_group)
        server_layout.setSpacing(10)

        self.auto_discover = QCheckBox("Auto-discover from domain name")
        self.auto_discover.setChecked(True)
        self.auto_discover.toggled.connect(self._on_auto_discover_toggled)
        server_layout.addRow("", self.auto_discover)

        self.domain_input = QLineEdit()
        self.domain_input.setPlaceholderText("e.g., example.com or corp.example.com")
        server_layout.addRow("Domain:", self.domain_input)

        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText("e.g., dc01.example.com or 192.168.1.10")
        self.server_input.setEnabled(False)
        server_layout.addRow("Server:", self.server_input)

        port_layout = QHBoxLayout()
        self.port_input = QLineEdit("636")
        self.port_input.setMaximumWidth(100)
        port_layout.addWidget(self.port_input)

        self.ssl_check = QCheckBox("Use SSL/LDAPS")
        self.ssl_check.setChecked(True)
        self.ssl_check.toggled.connect(self._on_ssl_toggled)
        port_layout.addWidget(self.ssl_check)
        port_layout.addStretch()

        server_layout.addRow("Port:", port_layout)

        self.timeout_input = QLineEdit("30")
        self.timeout_input.setMaximumWidth(100)
        server_layout.addRow("Timeout (s):", self.timeout_input)

        layout.addWidget(server_group)

        # Credentials group
        creds_group = QGroupBox("Credentials")
        creds_layout = QFormLayout(creds_group)
        creds_layout.setSpacing(10)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("e.g., administrator or DOMAIN\\username")
        creds_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Password")
        self.password_input.returnPressed.connect(self._on_connect)
        creds_layout.addRow("Password:", self.password_input)

        self.show_password = QCheckBox("Show password")
        self.show_password.toggled.connect(self._on_show_password_toggled)
        creds_layout.addRow("", self.show_password)

        self.save_password = QCheckBox("Remember password")
        self.save_password.setChecked(False)
        creds_layout.addRow("", self.save_password)

        layout.addWidget(creds_group)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"color: {COLORS['danger']}; font-size: 12px;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {COLORS['info']}; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addSpacerItem(QSpacerItem(0, 8, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.test_btn = QPushButton("Test Connection")
        self.test_btn.setObjectName("SecondaryButton")
        self.test_btn.setMinimumHeight(38)
        self.test_btn.setMinimumWidth(140)
        self.test_btn.clicked.connect(self._on_test)
        btn_layout.addWidget(self.test_btn)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setMinimumHeight(38)
        self.connect_btn.setMinimumWidth(120)
        self.connect_btn.clicked.connect(self._on_connect)
        btn_layout.addWidget(self.connect_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("SecondaryButton")
        self.cancel_btn.setMinimumHeight(38)
        self.cancel_btn.setMinimumWidth(100)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

    def _on_auto_discover_toggled(self, checked):
        self.server_input.setEnabled(not checked)

    def _on_ssl_toggled(self, checked):
        self.port_input.setText("636" if checked else "389")

    def _on_show_password_toggled(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(mode)

    def _get_config(self) -> ADConfig:
        """Get the ADConfig from form inputs."""
        return ADConfig(
            server=self.server_input.text().strip(),
            port=int(self.port_input.text() or "636"),
            use_ssl=self.ssl_check.isChecked(),
            domain=self.domain_input.text().strip(),
            base_dn="",
            username=self.username_input.text().strip(),
            password=self.password_input.text(),
            timeout=int(self.timeout_input.text() or "30"),
            auto_discover=self.auto_discover.isChecked(),
        )

    def _on_test(self):
        """Test the connection without closing the dialog."""
        self.error_label.clear()
        self.status_label.setText("Testing connection...")
        self.test_btn.setEnabled(False)
        self.connect_btn.setEnabled(False)

        config = self._get_config()

        if not config.domain and not config.server:
            self.error_label.setText("Please enter a domain or server address.")
            self.test_btn.setEnabled(True)
            self.connect_btn.setEnabled(True)
            self.status_label.clear()
            return

        if not config.username:
            self.error_label.setText("Please enter a username.")
            self.test_btn.setEnabled(True)
            self.connect_btn.setEnabled(True)
            self.status_label.clear()
            return

        # Test connection
        from core.ad_connection import ADConnection
        test_conn = ADConnection()

        try:
            success, message = test_conn.connect(config)
            if success:
                test_conn.disconnect()
                self.status_label.setText(f"✅ {message}")
                self.error_label.clear()
            else:
                self.error_label.setText(message)
                self.status_label.clear()
        except Exception as e:
            self.error_label.setText(f"Error: {str(e)}")
            self.status_label.clear()
        finally:
            self.test_btn.setEnabled(True)
            self.connect_btn.setEnabled(True)

    def _on_connect(self):
        """Attempt to connect and emit the config."""
        self.error_label.clear()

        config = self._get_config()

        if not config.domain and not config.server:
            self.error_label.setText("Please enter a domain or server address.")
            return

        if not config.username:
            self.error_label.setText("Please enter a username.")
            return

        if not config.password:
            self.error_label.setText("Please enter a password.")
            return

        # Save settings
        self._save_settings()

        self.connection_requested.emit(config)

    def _save_settings(self):
        """Save connection settings."""
        self.settings.setValue("domain", self.domain_input.text())
        self.settings.setValue("server", self.server_input.text())
        self.settings.setValue("port", self.port_input.text())
        self.settings.setValue("use_ssl", self.ssl_check.isChecked())
        self.settings.setValue("auto_discover", self.auto_discover.isChecked())
        self.settings.setValue("username", self.username_input.text())
        self.settings.setValue("timeout", self.timeout_input.text())

        if self.save_password.isChecked():
            self.settings.setValue("password", self.password_input.text())
        else:
            self.settings.remove("password")

    def _load_settings(self):
        """Load saved connection settings."""
        self.domain_input.setText(self.settings.value("domain", ""))
        self.server_input.setText(self.settings.value("server", ""))
        self.port_input.setText(self.settings.value("port", "636"))
        self.ssl_check.setChecked(self.settings.value("use_ssl", True, type=bool))
        self.auto_discover.setChecked(self.settings.value("auto_discover", True, type=bool))
        self.username_input.setText(self.settings.value("username", ""))
        self.timeout_input.setText(self.settings.value("timeout", "30"))

        saved_password = self.settings.value("password", "")
        if saved_password:
            self.password_input.setText(saved_password)
            self.save_password.setChecked(True)

        # Trigger auto-discover toggle
        self._on_auto_discover_toggled(self.auto_discover.isChecked())

    def show_error(self, message: str):
        """Show an error message."""
        self.error_label.setText(f"❌ {message}")

    def show_status(self, message: str):
        """Show a status message."""
        self.status_label.setText(message)
