"""
Reports and Dashboard panel for the AD Manager.
Provides overview and common reports.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QTabWidget, QFrame, QAbstractItemView, QComboBox,
    QTextEdit, QSplitter, QScrollArea, QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QColor, QFont

from core.ad_connection import ADConnection, ADUserInfo
from ui.widgets import DetailPanel, ResultMessageBox
from ui.styles import COLORS
from utils.helpers import format_ad_date, extract_cn_from_dn


class StatCard(QFrame):
    """A statistics card showing a number and label."""

    def __init__(self, title: str, value: str = "0", icon: str = "📊", parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 16px;
            }}
            QFrame:hover {{
                border-color: {COLORS['primary']};
            }}
        """)
        self.setMinimumHeight(100)
        self.setMinimumWidth(180)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Icon + Title
        header = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 24px;")
        header.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        header.addWidget(title_label)
        header.addStretch()
        layout.addLayout(header)

        # Value
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(self.value_label)

    def set_value(self, value: str):
        self.value_label.setText(value)


class ReportsPanel(QWidget):
    """Dashboard and Reports panel."""

    status_message = pyqtSignal(str)

    def __init__(self, ad: ADConnection, parent=None):
        super().__init__(parent)
        self.ad = ad

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Dashboard header
        header = QLabel("📊 Dashboard Overview")
        header.setStyleSheet("font-size: 24px; font-weight: bold; padding: 8px 0;")
        main_layout.addWidget(header)

        # Stats cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.total_users_card = StatCard("Total Users", "...", "👤")
        stats_layout.addWidget(self.total_users_card)

        self.enabled_users_card = StatCard("Enabled", "...", "✅")
        stats_layout.addWidget(self.enabled_users_card)

        self.disabled_users_card = StatCard("Disabled", "...", "🚫")
        stats_layout.addWidget(self.disabled_users_card)

        self.locked_users_card = StatCard("Locked Out", "...", "🔒")
        stats_layout.addWidget(self.locked_users_card)

        self.total_computers_card = StatCard("Computers", "...", "🖥️")
        stats_layout.addWidget(self.total_computers_card)

        self.total_groups_card = StatCard("Groups", "...", "👥")
        stats_layout.addWidget(self.total_groups_card)

        self.total_gpos_card = StatCard("GPOs", "...", "📋")
        stats_layout.addWidget(self.total_gpos_card)

        stats_layout.addStretch()
        main_layout.addLayout(stats_layout)

        # Refresh button
        refresh_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Refresh Dashboard")
        refresh_btn.setMinimumHeight(36)
        refresh_btn.clicked.connect(self.refresh)
        refresh_layout.addWidget(refresh_btn)
        refresh_layout.addStretch()
        main_layout.addLayout(refresh_layout)

        # Tabs for reports
        tabs = QTabWidget()

        # Locked accounts report
        locked_tab = self._create_report_tab(
            "🔒 Locked Accounts",
            "locked",
            ["Username", "Display Name", "Email", "Department", "Last Modified", "DN"],
        )
        tabs.addTab(locked_tab, "🔒 Locked Accounts")

        # Disabled accounts report
        disabled_tab = self._create_report_tab(
            "🚫 Disabled Accounts",
            "disabled",
            ["Username", "Display Name", "Email", "Department", "Last Modified", "DN"],
        )
        tabs.addTab(disabled_tab, "🚫 Disabled Accounts")

        # Disabled computers report
        disabled_pc_tab = self._create_report_tab(
            "🖥️ Disabled Computers",
            "disabled_computers",
            ["Name", "DNS Hostname", "OS", "Description", "Created", "DN"],
        )
        tabs.addTab(disabled_pc_tab, "🖥️ Disabled Computers")

        # Never logged on
        never_tab = self._create_report_tab(
            "👤 Never Logged On",
            "never_logged_on",
            ["Username", "Display Name", "Email", "Department", "Created", "DN"],
        )
        tabs.addTab(never_tab, "👤 Never Logged On")

        # Password expired
        expired_tab = self._create_report_tab(
            "⏰ Password Expired",
            "password_expired",
            ["Username", "Display Name", "Email", "Department", "Modified", "DN"],
        )
        tabs.addTab(expired_tab, "⏰ Password Expired")

        # Export tab
        export_tab = self._create_export_tab()
        tabs.addTab(export_tab, "📤 Export")

        main_layout.addWidget(tabs, 1)

    def _create_report_tab(self, title: str, report_type: str, columns: list) -> QWidget:
        """Create a tab for a specific report."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header with count
        header_layout = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        header_layout.addWidget(title_label)

        self.count_label = QLabel("Loading...")
        self.count_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(self.count_label)
        header_layout.addStretch()

        export_csv_btn = QPushButton("📤 Export CSV")
        export_csv_btn.setObjectName("SecondaryButton")
        export_csv_btn.setMinimumHeight(32)
        export_csv_btn.clicked.connect(lambda: self._export_to_csv(report_type))
        header_layout.addWidget(export_csv_btn)

        layout.addLayout(header_layout)

        # Table
        table = QTableWidget()
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)

        header = table.horizontalHeader()
        for i in range(len(columns)):
            if i == 0:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            elif i < len(columns) - 2:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)

        layout.addWidget(table, 1)

        # Store references
        setattr(self, f"_{report_type}_table", table)
        setattr(self, f"_{report_type}_count", self.count_label)

        return widget

    def _create_export_tab(self) -> QWidget:
        """Create the export tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        title = QLabel("📤 Export Data")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        info = QLabel(
            "Export AD data to CSV files for analysis, reporting, or auditing.\n"
            "Select the data type and click Export."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(info)

        # Export options
        export_grid = QGridLayout()
        export_grid.setSpacing(12)

        # Users export
        users_card = QFrame()
        users_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        users_layout = QVBoxLayout(users_card)
        users_title = QLabel("👤 Export Users")
        users_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        users_layout.addWidget(users_title)
        users_desc = QLabel("Export all user accounts with attributes")
        users_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        users_layout.addWidget(users_desc)
        users_btn = QPushButton("Export Users")
        users_btn.setMinimumHeight(32)
        users_btn.clicked.connect(lambda: self._export_to_csv("all_users"))
        users_layout.addWidget(users_btn)
        export_grid.addWidget(users_card, 0, 0)

        # Computers export
        pc_card = QFrame()
        pc_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        pc_layout = QVBoxLayout(pc_card)
        pc_title = QLabel("🖥️ Export Computers")
        pc_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        pc_layout.addWidget(pc_title)
        pc_desc = QLabel("Export all computer/workstation accounts")
        pc_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        pc_layout.addWidget(pc_desc)
        pc_btn = QPushButton("Export Computers")
        pc_btn.setMinimumHeight(32)
        pc_btn.clicked.connect(lambda: self._export_to_csv("all_computers"))
        pc_layout.addWidget(pc_btn)
        export_grid.addWidget(pc_card, 0, 1)

        # Groups export
        groups_card = QFrame()
        groups_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        groups_layout = QVBoxLayout(groups_card)
        groups_title = QLabel("👥 Export Groups")
        groups_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        groups_layout.addWidget(groups_title)
        groups_desc = QLabel("Export all security and distribution groups")
        groups_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        groups_layout.addWidget(groups_desc)
        groups_btn = QPushButton("Export Groups")
        groups_btn.setMinimumHeight(32)
        groups_btn.clicked.connect(lambda: self._export_to_csv("all_groups"))
        groups_layout.addWidget(groups_btn)
        export_grid.addWidget(groups_card, 0, 2)

        # GPOs export
        gpo_card = QFrame()
        gpo_card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['card_bg']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        gpo_layout = QVBoxLayout(gpo_card)
        gpo_title = QLabel("📋 Export GPOs")
        gpo_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        gpo_layout.addWidget(gpo_title)
        gpo_desc = QLabel("Export all Group Policy Objects")
        gpo_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        gpo_layout.addWidget(gpo_desc)
        gpo_btn = QPushButton("Export GPOs")
        gpo_btn.setMinimumHeight(32)
        gpo_btn.clicked.connect(lambda: self._export_to_csv("all_gpos"))
        gpo_layout.addWidget(gpo_btn)
        export_grid.addWidget(gpo_card, 0, 3)

        layout.addLayout(export_grid)

        # Output area
        output_group = QGroupBox("Export Output")
        output_layout = QVBoxLayout(output_group)
        self.export_output = QTextEdit()
        self.export_output.setReadOnly(True)
        self.export_output.setMaximumHeight(200)
        output_layout.addWidget(self.export_output)
        layout.addWidget(output_group)

        layout.addStretch()

        return widget

    def refresh(self):
        """Refresh all dashboard data."""
        if not self.ad.is_connected:
            return

        self.status_message.emit("Loading dashboard data...")
        QTimer.singleShot(100, self._do_refresh)

    def _do_refresh(self):
        """Perform the actual refresh."""
        try:
            # Get stats
            all_users = self.ad.search_users("*")
            enabled_users = [u for u in all_users if u.enabled]
            disabled_users = [u for u in all_users if not u.enabled]

            all_computers = self.ad.search_computers("*")
            all_groups = self.ad.search_groups("*")
            all_gpos = self.ad.get_all_gpos()

            locked_users = self.ad.get_locked_accounts()

            # Update cards
            self.total_users_card.set_value(str(len(all_users)))
            self.enabled_users_card.set_value(str(len(enabled_users)))
            self.disabled_users_card.set_value(str(len(disabled_users)))
            self.locked_users_card.set_value(str(len(locked_users)))
            self.total_computers_card.set_value(str(len(all_computers)))
            self.total_groups_card.set_value(str(len(all_groups)))
            self.total_gpos_card.set_value(str(len(all_gpos)))

            # Populate locked accounts
            self._populate_users_report(
                "_locked_table", locked_users, "locked"
            )

            # Populate disabled accounts
            self._populate_users_report(
                "_disabled_table", disabled_users, "disabled"
            )

            # Populate disabled computers
            self._populate_computers_report(
                "_disabled_computers_table",
                self.ad.get_disabled_computers(),
                "disabled_computers",
            )

            # Populate never logged on
            try:
                never_logged = self.ad.get_never_logged_on()
                self._populate_users_report(
                    "_never_logged_on_table", never_logged, "never_logged_on"
                )
            except Exception:
                pass

            # Populate password expired
            try:
                expired = self.ad.get_password_expired_users()
                self._populate_users_report(
                    "_password_expired_table", expired, "password_expired"
                )
            except Exception:
                pass

            self.status_message.emit("Dashboard refreshed successfully")

        except Exception as e:
            self.status_message.emit(f"Dashboard error: {str(e)}")

    def _populate_users_report(self, table_attr: str, users: list, report_type: str):
        """Populate a users report table."""
        table = getattr(self, table_attr, None)
        count_label = getattr(self, f"_{report_type}_count", None)

        if not table:
            return

        table.setSortingEnabled(False)
        table.setRowCount(0)

        for user in users:
            row = table.rowCount()
            table.insertRow(row)

            table.setItem(row, 0, QTableWidgetItem(user.sam_account_name))
            table.setItem(row, 1, QTableWidgetItem(user.display_name))
            table.setItem(row, 2, QTableWidgetItem(user.email))
            table.setItem(row, 3, QTableWidgetItem(user.department))
            table.setItem(row, 4, QTableWidgetItem(format_ad_date(user.when_changed)))
            table.setItem(row, 5, QTableWidgetItem(user.dn))

        table.setSortingEnabled(True)

        if count_label:
            count_label.setText(f"{len(users)} found")

    def _populate_computers_report(self, table_attr: str, computers: list, report_type: str):
        """Populate a computers report table."""
        table = getattr(self, table_attr, None)
        count_label = getattr(self, f"_{report_type}_count", None)

        if not table:
            return

        table.setSortingEnabled(False)
        table.setRowCount(0)

        for computer in computers:
            row = table.rowCount()
            table.insertRow(row)

            table.setItem(row, 0, QTableWidgetItem(computer.name))
            table.setItem(row, 1, QTableWidgetItem(computer.dns_host_name))
            table.setItem(row, 2, QTableWidgetItem(computer.operating_system))
            table.setItem(row, 3, QTableWidgetItem(computer.description))
            table.setItem(row, 4, QTableWidgetItem(format_ad_date(computer.when_created)))
            table.setItem(row, 5, QTableWidgetItem(computer.dn))

        table.setSortingEnabled(True)

        if count_label:
            count_label.setText(f"{len(computers)} found")

    def _export_to_csv(self, report_type: str):
        """Export report data to CSV."""
        from PyQt6.QtWidgets import QFileDialog
        import csv

        # Determine filename
        filenames = {
            "locked": "locked_accounts.csv",
            "disabled": "disabled_accounts.csv",
            "disabled_computers": "disabled_computers.csv",
            "never_logged_on": "never_logged_on.csv",
            "password_expired": "password_expired.csv",
            "all_users": "all_users.csv",
            "all_computers": "all_computers.csv",
            "all_groups": "all_groups.csv",
            "all_gpos": "all_gpos.csv",
        }

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export to CSV",
            filenames.get(report_type, "export.csv"),
            "CSV Files (*.csv);;All Files (*)"
        )

        if not filename:
            return

        try:
            if report_type == "locked":
                data = self.ad.get_locked_accounts()
                self._export_users_csv(filename, data)
            elif report_type == "disabled":
                data = self.ad.get_disabled_accounts()
                self._export_users_csv(filename, data)
            elif report_type == "disabled_computers":
                data = self.ad.get_disabled_computers()
                self._export_computers_csv(filename, data)
            elif report_type == "never_logged_on":
                data = self.ad.get_never_logged_on()
                self._export_users_csv(filename, data)
            elif report_type == "password_expired":
                data = self.ad.get_password_expired_users()
                self._export_users_csv(filename, data)
            elif report_type == "all_users":
                data = self.ad.search_users("*")
                self._export_users_csv(filename, data)
            elif report_type == "all_computers":
                data = self.ad.search_computers("*")
                self._export_computers_csv(filename, data)
            elif report_type == "all_groups":
                data = self.ad.search_groups("*")
                self._export_groups_csv(filename, data)
            elif report_type == "all_gpos":
                data = self.ad.get_all_gpos()
                self._export_gpos_csv(filename, data)

            self.export_output.append(f"✅ Exported to: {filename}")
            self.status_message.emit(f"Exported to {filename}")

        except Exception as e:
            self.export_output.append(f"❌ Export error: {str(e)}")
            self.status_message.emit(f"Export error: {str(e)}")

    def _export_users_csv(self, filename: str, users: list):
        """Export users to CSV."""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Username", "Display Name", "First Name", "Last Name",
                "Email", "Department", "Title", "Office", "Phone", "Mobile",
                "Enabled", "Locked", "Description", "Created", "Modified", "DN"
            ])
            for user in users:
                writer.writerow([
                    user.sam_account_name, user.display_name,
                    user.given_name, user.sn, user.email,
                    user.department, user.title, user.office,
                    user.telephone, user.mobile,
                    "Yes" if user.enabled else "No",
                    "Yes" if user.locked_out else "No",
                    user.description,
                    format_ad_date(user.when_created),
                    format_ad_date(user.when_changed),
                    user.dn,
                ])

    def _export_computers_csv(self, filename: str, computers: list):
        """Export computers to CSV."""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Name", "SAM Account", "DNS Hostname", "OS",
                "Description", "Enabled", "Location", "Managed By",
                "Created", "Modified", "DN"
            ])
            for pc in computers:
                writer.writerow([
                    pc.name, pc.sam_account_name, pc.dns_host_name,
                    pc.operating_system, pc.description,
                    "Yes" if pc.enabled else "No",
                    pc.location, extract_cn_from_dn(pc.managed_by) if pc.managed_by else "",
                    format_ad_date(pc.when_created),
                    format_ad_date(pc.when_changed),
                    pc.dn,
                ])

    def _export_groups_csv(self, filename: str, groups: list):
        """Export groups to CSV."""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Name", "SAM Account", "Description", "Scope",
                "Type", "Member Count", "Email", "Managed By",
                "Created", "Modified", "DN"
            ])
            for group in groups:
                writer.writerow([
                    group.name, group.sam_account_name, group.description,
                    group.group_scope, group.group_type,
                    group.member_count, group.email,
                    extract_cn_from_dn(group.managed_by) if group.managed_by else "",
                    format_ad_date(group.when_created),
                    format_ad_date(group.when_changed),
                    group.dn,
                ])

    def _export_gpos_csv(self, filename: str, gpos: list):
        """Export GPOs to CSV."""
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Display Name", "Name", "Description", "Version",
                "File System Path", "Created", "Modified", "DN"
            ])
            for gpo in gpos:
                writer.writerow([
                    gpo.display_name, gpo.name, gpo.description,
                    gpo.version, gpo.gpc_file_system_path,
                    format_ad_date(gpo.when_created),
                    format_ad_date(gpo.when_changed),
                    gpo.dn,
                ])
