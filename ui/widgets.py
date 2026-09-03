"""
Custom widgets for the AD Manager application.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QFrame, QMessageBox, QProgressBar, QTextEdit, QGroupBox,
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QSpinBox, QSizePolicy, QStyledItemDelegate, QStyle,
    QApplication, QAbstractItemView,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QIcon, QPainter, QPixmap

from ui.styles import COLORS


class StatusBadge(QLabel):
    """A colored status badge label."""

    STYLES = {
        'success': ('background-color: #e6f4ea; color: #137333; border-radius: 12px; padding: 4px 12px; font-size: 12px; font-weight: bold;'),
        'error': ('background-color: #fce8e6; color: #c5221f; border-radius: 12px; padding: 4px 12px; font-size: 12px; font-weight: bold;'),
        'warning': ('background-color: #fef7e0; color: #e37400; border-radius: 12px; padding: 4px 12px; font-size: 12px; font-weight: bold;'),
        'info': ('background-color: #e8f0fe; color: #1967d2; border-radius: 12px; padding: 4px 12px; font-size: 12px; font-weight: bold;'),
        'disabled': ('background-color: #f1f3f4; color: #80868b; border-radius: 12px; padding: 4px 12px; font-size: 12px; font-weight: bold;'),
    }

    def __init__(self, text: str = "", style: str = "info", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(self.STYLES.get(style, self.STYLES['info']))
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(28)


class SearchBar(QWidget):
    """Reusable search bar with filter options."""

    search_triggered = pyqtSignal(str, str)  # query, field
    clear_triggered = pyqtSignal()

    def __init__(
        self,
        placeholder: str = "Search...",
        fields: list = None,
        parent=None,
    ):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Search icon label
        icon_label = QLabel("🔍")
        icon_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon_label)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(placeholder)
        self.search_input.setMinimumHeight(36)
        self.search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_input, 1)

        # Filter field combo
        if fields:
            self.field_combo = QComboBox()
            self.field_combo.addItems(fields)
            self.field_combo.setMinimumHeight(36)
            self.field_combo.setMinimumWidth(150)
            layout.addWidget(self.field_combo)
        else:
            self.field_combo = None

        # Search button
        self.search_btn = QPushButton("Search")
        self.search_btn.setMinimumHeight(36)
        self.search_btn.setMinimumWidth(80)
        self.search_btn.clicked.connect(self._on_search)
        layout.addWidget(self.search_btn)

        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("SecondaryButton")
        self.clear_btn.setMinimumHeight(36)
        self.clear_btn.setMinimumWidth(70)
        self.clear_btn.clicked.connect(self._on_clear)
        layout.addWidget(self.clear_btn)

    def _on_search(self):
        query = self.search_input.text().strip()
        field = self.field_combo.currentText() if self.field_combo else "sAMAccountName"
        self.search_triggered.emit(query, field)

    def _on_clear(self):
        self.search_input.clear()
        self.clear_btn.setFocus()
        self.clear_triggered.emit()

    def get_query(self) -> str:
        return self.search_input.text().strip()

    def set_query(self, text: str):
        self.search_input.setText(text)


class InfoCard(QFrame):
    """A card widget with title and content."""

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        if title:
            self.title_label = QLabel(title)
            self.title_label.setObjectName("CardTitle")
            layout.addWidget(self.title_label)
        else:
            self.title_label = None

        self.content_layout = layout

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)

    def add_stretch(self):
        self.content_layout.addStretch()


class DetailPanel(QWidget):
    """A detail panel showing key-value pairs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(4)
        self._fields = {}

    def add_field(self, key: str, value: str = "", bold_value: bool = False):
        """Add a key-value field."""
        row = QHBoxLayout()
        row.setSpacing(12)

        key_label = QLabel(f"{key}:")
        key_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; min-width: 140px;")
        key_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        row.addWidget(key_label)

        value_label = QLabel(str(value) if value else "N/A")
        if bold_value:
            value_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        else:
            value_label.setStyleSheet("font-size: 13px;")
        value_label.setWordWrap(True)
        row.addWidget(value_label, 1)

        self._fields[key] = value_label
        self.layout.addLayout(row)

    def add_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS['border_light']}; max-height: 1px;")
        self.layout.addWidget(line)

    def update_field(self, key: str, value: str):
        """Update a field's value."""
        if key in self._fields:
            self._fields[key].setText(str(value) if value else "N/A")

    def clear(self):
        """Clear all fields."""
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub_item = item.layout().takeAt(0)
                    if sub_item.widget():
                        sub_item.widget().deleteLater()
        self._fields.clear()


class ResultMessageBox:
    """Helper to show result messages."""

    @staticmethod
    def success(parent, title: str, message: str):
        QMessageBox.information(parent, title, message)

    @staticmethod
    def error(parent, title: str, message: str):
        QMessageBox.critical(parent, title, message)

    @staticmethod
    def warning(parent, title: str, message: str):
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def question(parent, title: str, message: str) -> bool:
        reply = QMessageBox.question(
            parent, title, message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes


class PasswordInput(QDialog):
    """Dialog for entering a new password."""

    def __init__(self, title: str = "Set Password", username: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setModal(True)

        layout = QVBoxLayout(self)

        if username:
            info = QLabel(f"Setting password for: <b>{username}</b>")
            info.setStyleSheet("font-size: 14px; padding: 8px 0;")
            layout.addWidget(info)

        form = QFormLayout()

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter new password")
        form.addRow("Password:", self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Confirm password")
        self.confirm_input.returnPressed.connect(self._on_accept)
        form.addRow("Confirm:", self.confirm_input)

        self.show_password = QCheckBox("Show password")
        self.show_password.toggled.connect(self._toggle_password_visibility)
        form.addRow("", self.show_password)

        self.must_change = QCheckBox("User must change password at next logon")
        self.must_change.setChecked(True)
        form.addRow("", self.must_change)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Focus password input
        self.password_input.setFocus()

    def _toggle_password_visibility(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(mode)
        self.confirm_input.setEchoMode(mode)

    def _on_accept(self):
        if not self.password_input.text():
            QMessageBox.warning(self, "Error", "Password cannot be empty.")
            return

        if self.password_input.text() != self.confirm_input.text():
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return

        if len(self.password_input.text()) < 7:
            QMessageBox.warning(self, "Error", "Password must be at least 7 characters.")
            return

        self.accept()

    def get_password(self) -> str:
        return self.password_input.text()

    def must_change_password(self) -> bool:
        return self.must_change.isChecked()


class CreateUserDialog(QDialog):
    """Dialog for creating a new user."""

    def __init__(self, ous: list = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New User")
        self.setMinimumWidth(500)
        self.setMinimumHeight(500)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Form
        form = QFormLayout()
        form.setSpacing(10)

        self.sam_input = QLineEdit()
        self.sam_input.setPlaceholderText("e.g., jsmith")
        form.addRow("Username *:", self.sam_input)

        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("First name")
        form.addRow("First Name *:", self.first_name_input)

        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Last name")
        form.addRow("Last Name *:", self.last_name_input)

        self.display_name_input = QLineEdit()
        self.display_name_input.setPlaceholderText("Auto-generated if empty")
        form.addRow("Display Name:", self.display_name_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("user@domain.com")
        form.addRow("Email:", self.email_input)

        self.ou_combo = QComboBox()
        if ous:
            for ou in ous:
                self.ou_combo.addItem(ou.name, ou.dn)
        form.addRow("Organizational Unit *:", self.ou_combo)

        self.department_input = QLineEdit()
        form.addRow("Department:", self.department_input)

        self.title_input = QLineEdit()
        form.addRow("Title:", self.title_input)

        self.description_input = QLineEdit()
        form.addRow("Description:", self.description_input)

        # Password section
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Minimum 7 characters")
        form.addRow("Password *:", self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Confirm Password *:", self.confirm_input)

        self.show_password = QCheckBox("Show password")
        self.show_password.toggled.connect(self._toggle_visibility)
        form.addRow("", self.show_password)

        self.must_change = QCheckBox("Must change password at next logon")
        self.must_change.setChecked(True)
        form.addRow("", self.must_change)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Create User")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _toggle_visibility(self, checked):
        mode = QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        self.password_input.setEchoMode(mode)
        self.confirm_input.setEchoMode(mode)

    def _on_accept(self):
        if not self.sam_input.text().strip():
            QMessageBox.warning(self, "Error", "Username is required.")
            return
        if not self.first_name_input.text().strip():
            QMessageBox.warning(self, "Error", "First name is required.")
            return
        if not self.last_name_input.text().strip():
            QMessageBox.warning(self, "Error", "Last name is required.")
            return
        if not self.password_input.text():
            QMessageBox.warning(self, "Error", "Password is required.")
            return
        if self.password_input.text() != self.confirm_input.text():
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
        if len(self.password_input.text()) < 7:
            QMessageBox.warning(self, "Error", "Password must be at least 7 characters.")
            return

        self.accept()

    def get_data(self) -> dict:
        display_name = self.display_name_input.text().strip()
        if not display_name:
            display_name = f"{self.first_name_input.text().strip()} {self.last_name_input.text().strip()}"

        return {
            'sam_account_name': self.sam_input.text().strip(),
            'first_name': self.first_name_input.text().strip(),
            'last_name': self.last_name_input.text().strip(),
            'display_name': display_name,
            'email': self.email_input.text().strip(),
            'ou_dn': self.ou_combo.currentData(),
            'department': self.department_input.text().strip(),
            'title': self.title_input.text().strip(),
            'description': self.description_input.text().strip(),
            'password': self.password_input.text(),
            'must_change_password': self.must_change.isChecked(),
        }


class CloneUserDialog(QDialog):
    """Dialog for cloning a user."""

    def __init__(self, source_user=None, ous: list = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Clone User")
        self.setMinimumWidth(500)
        self.setModal(True)

        layout = QVBoxLayout(self)

        # Source user info
        if source_user:
            source_info = QGroupBox("Source User")
            source_layout = QFormLayout(source_info)
            source_layout.addRow("Username:", QLabel(source_user.sam_account_name))
            source_layout.addRow("Name:", QLabel(source_user.display_name))
            source_layout.addRow("Department:", QLabel(source_user.department or "N/A"))
            source_layout.addRow("Title:", QLabel(source_user.title or "N/A"))
            layout.addWidget(source_info)

        # New user form
        form = QFormLayout()
        form.setSpacing(10)

        self.sam_input = QLineEdit()
        self.sam_input.setPlaceholderText("New username")
        form.addRow("New Username *:", self.sam_input)

        self.first_name_input = QLineEdit()
        self.first_name_input.setPlaceholderText("First name")
        form.addRow("First Name *:", self.first_name_input)

        self.last_name_input = QLineEdit()
        self.last_name_input.setPlaceholderText("Last name")
        form.addRow("Last Name *:", self.last_name_input)

        self.ou_combo = QComboBox()
        if ous:
            for ou in ous:
                self.ou_combo.addItem(ou.name, ou.dn)
        form.addRow("Target OU:", self.ou_combo)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Minimum 7 characters")
        form.addRow("Password *:", self.password_input)

        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Confirm Password *:", self.confirm_input)

        self.copy_groups = QCheckBox("Copy group memberships")
        self.copy_groups.setChecked(True)
        form.addRow("", self.copy_groups)

        self.must_change = QCheckBox("Must change password at next logon")
        self.must_change.setChecked(True)
        form.addRow("", self.must_change)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Clone User")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        if not self.sam_input.text().strip():
            QMessageBox.warning(self, "Error", "New username is required.")
            return
        if not self.first_name_input.text().strip():
            QMessageBox.warning(self, "Error", "First name is required.")
            return
        if not self.last_name_input.text().strip():
            QMessageBox.warning(self, "Error", "Last name is required.")
            return
        if not self.password_input.text():
            QMessageBox.warning(self, "Error", "Password is required.")
            return
        if self.password_input.text() != self.confirm_input.text():
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return
        if len(self.password_input.text()) < 7:
            QMessageBox.warning(self, "Error", "Password must be at least 7 characters.")
            return

        self.accept()

    def get_data(self) -> dict:
        return {
            'new_sam': self.sam_input.text().strip(),
            'new_first_name': self.first_name_input.text().strip(),
            'new_last_name': self.last_name_input.text().strip(),
            'new_password': self.password_input.text(),
            'ou_dn': self.ou_combo.currentData(),
            'copy_groups': self.copy_groups.isChecked(),
            'must_change': self.must_change.isChecked(),
        }


class CreateGroupDialog(QDialog):
    """Dialog for creating a new group."""

    def __init__(self, ous: list = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Group")
        self.setMinimumWidth(450)
        self.setModal(True)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Group name")
        form.addRow("Group Name *:", self.name_input)

        self.ou_combo = QComboBox()
        if ous:
            for ou in ous:
                self.ou_combo.addItem(ou.name, ou.dn)
        form.addRow("Organizational Unit *:", self.ou_combo)

        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Description (optional)")
        form.addRow("Description:", self.description_input)

        self.scope_combo = QComboBox()
        self.scope_combo.addItems(["Global", "DomainLocal", "Universal"])
        form.addRow("Scope:", self.scope_combo)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Security", "Distribution"])
        form.addRow("Type:", self.type_combo)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Create Group")
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Error", "Group name is required.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            'name': self.name_input.text().strip(),
            'ou_dn': self.ou_combo.currentData(),
            'description': self.description_input.text().strip(),
            'scope': self.scope_combo.currentText(),
            'group_type': self.type_combo.currentText(),
        }


class LoadingOverlay(QWidget):
    """Overlay widget that shows a loading spinner."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel("Loading...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet(f"""
            background-color: rgba(255, 255, 255, 200);
            color: {COLORS['text_primary']};
            font-size: 16px;
            font-weight: bold;
            padding: 20px;
            border-radius: 8px;
        """)
        layout.addWidget(self.label)

        self.hide()

    def show_loading(self, text: str = "Loading..."):
        self.label.setText(f"⏳ {text}")
        self.show()
        self.raise_()

    def hide_loading(self):
        self.hide()
