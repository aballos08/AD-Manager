"""
Audit Trail viewer panel for the AD Manager.

Displays every recorded AD change (who/when/what/result) with text
search, column filters, hash-chain verification, and CSV export.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QFileDialog, QAbstractItemView, QMessageBox,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from core.audit import AuditLog
from core.ad_connection import ADConnection
from ui.styles import COLORS


ACTION_LABELS = {
    "create": "➕ Create",
    "delete": "🗑️ Delete",
    "modify": "✏️ Modify",
}


class AuditPanel(QWidget):
    """Audit trail viewer: who did what, when, and whether it succeeded."""

    status_message = pyqtSignal(str)

    def __init__(self, ad: ADConnection, parent=None):
        super().__init__(parent)
        self.ad = ad
        self.audit: AuditLog = ad.audit
        self._entries = []
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header
        header = QLabel("📜 Audit Trail")
        header.setStyleSheet("font-size: 24px; font-weight: bold; padding: 8px 0;")
        main_layout.addWidget(header)

        subtitle = QLabel(
            "Every AD change is recorded with operator, time (UTC), action, "
            "object, and outcome. Entries are hash-chained for tamper evidence."
        )
        subtitle.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        subtitle.setWordWrap(True)
        main_layout.addWidget(subtitle)

        # Toolbar
        toolbar = QHBoxLayout()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(
            "🔎 Search operator, object, or details…"
        )
        self.search_box.setMinimumHeight(32)
        self.search_box.setMinimumWidth(260)
        self.search_box.textChanged.connect(self._apply_filters)
        toolbar.addWidget(self.search_box)

        self.action_filter = QComboBox()
        self.action_filter.addItems(
            ["All actions", "create", "modify", "delete"]
        )
        self.action_filter.setMinimumHeight(32)
        self.action_filter.currentTextChanged.connect(self._apply_filters)
        toolbar.addWidget(self.action_filter)

        self.type_filter = QComboBox()
        self.type_filter.addItems(
            ["All types", "user", "group", "computer", "gpo", "ou"]
        )
        self.type_filter.setFixedHeight(32)
        self.type_filter.currentTextChanged.connect(self._apply_filters)
        toolbar.addWidget(self.type_filter)

        self.result_filter = QComboBox()
        self.result_filter.addItems(["All results", "success", "failure"])
        self.result_filter.setFixedHeight(32)
        self.result_filter.currentTextChanged.connect(self._apply_filters)
        toolbar.addWidget(self.result_filter)

        toolbar.addStretch()

        verify_btn = QPushButton("🧪 Verify chain")
        verify_btn.setObjectName("SecondaryButton")
        verify_btn.setMinimumHeight(32)
        verify_btn.clicked.connect(self._on_verify)
        toolbar.addWidget(verify_btn)

        export_btn = QPushButton("📤 Export CSV")
        export_btn.setObjectName("SecondaryButton")
        export_btn.setMinimumHeight(32)
        export_btn.clicked.connect(self._on_export_csv)
        toolbar.addWidget(export_btn)

        main_layout.addLayout(toolbar)

        # Chain status label
        self.chain_label = QLabel("")
        self.chain_label.setStyleSheet("font-size: 12px;")
        main_layout.addWidget(self.chain_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Time (UTC)", "Operator", "Action", "Type", "Object", "Details", "Result"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table, 1)

        # Footer info
        self.count_label = QLabel("0 entries")
        self.count_label.setStyleSheet(
            f"color: {COLORS['text_secondary']}; font-size: 12px;"
        )
        main_layout.addWidget(self.count_label)

    # ── data ──────────────────────────────────────────────────────

    def refresh(self):
        """Reload entries from disk and apply current filters."""
        try:
            self._entries = self.audit.load(limit=5000)
        except Exception as e:
            self._entries = []
            QMessageBox.warning(self, "Audit Log", f"Could not load audit log: {e}")
        self._apply_filters()

    def _apply_filters(self):
        search = self.search_box.text().strip().lower()
        action = self.action_filter.currentText()
        obj_type = self.type_filter.currentText()
        result = self.result_filter.currentText()

        rows = []
        for e in self._entries:
            if action != "All actions" and e.action != action:
                continue
            if obj_type != "All types" and e.object_type != obj_type:
                continue
            if result != "All results" and e.result != result:
                continue
            if search:
                haystack = " ".join(
                    [e.operator or "", e.object_name or "", e.details or ""]
                ).lower()
                if search not in haystack:
                    continue
            rows.append(e)

        # Newest first
        rows.reverse()

        self.table.setRowCount(len(rows))
        red = QColor("#e74c3c")
        green = QColor("#27ae60")
        for r, e in enumerate(rows):
            ts = e.timestamp.replace("T", " ").split(".")[0]
            values = [
                ts,
                e.operator or "?",
                ACTION_LABELS.get(e.action, e.action),
                e.object_type,
                e.object_name,
                e.details,
                e.result,
            ]
            for c, v in enumerate(values):
                item = QTableWidgetItem(str(v))
                if c == 6:
                    item.setForeground(green if e.result == "success" else red)
                if c == 2:
                    item.setForeground(
                        QColor("#c0392b") if e.action == "delete" else QColor(COLORS['text_primary'])
                    )
                self.table.setItem(r, c, item)

        self.count_label.setText(
            f"{len(rows)} entries shown (of {len(self._entries)} total)"
        )

    def _on_verify(self):
        report = self.audit.verify()
        if report["ok"]:
            self.chain_label.setText(
                f"✅ Hash chain intact — {report['total']} entries verified."
            )
            self.chain_label.setStyleSheet("color: #27ae60; font-size: 12px;")
        else:
            self.chain_label.setText(
                f"🚨 TAMPERING DETECTED at entry {report['broken_at'] + 1} "
                f"of {report['total']}."
            )
            self.chain_label.setStyleSheet("color: #e74c3c; font-size: 12px; font-weight: bold;")

    def _on_export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Audit Trail", "audit_trail.csv",
            "CSV files (*.csv);;All files (*)",
        )
        if not path:
            return
        try:
            count = self.audit.export_csv(path, self._entries)
            self.status_message.emit(f"Exported {count} audit entries to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Could not write CSV: {e}")
