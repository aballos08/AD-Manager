"""
Application styles and theming for the AD Manager.
"""

# Color palette
COLORS = {
    'primary': '#1a73e8',
    'primary_hover': '#1557b0',
    'primary_pressed': '#0d47a1',
    'secondary': '#5f6368',
    'success': '#34a853',
    'warning': '#fbbc04',
    'danger': '#ea4335',
    'info': '#4285f4',
    'background': '#f8f9fa',
    'surface': '#ffffff',
    'surface_variant': '#f1f3f4',
    'text_primary': '#202124',
    'text_secondary': '#5f6368',
    'border': '#dadce0',
    'border_light': '#e8eaed',
    'sidebar_bg': '#1a1d21',
    'sidebar_text': '#e8eaed',
    'sidebar_hover': '#2d3139',
    'sidebar_active': '#1a73e8',
    'header_bg': '#ffffff',
    'card_bg': '#ffffff',
}

MAIN_STYLESHEET = f"""
/* Global */
QWidget {{
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
    color: {COLORS['text_primary']};
    background-color: {COLORS['background']};
}}

/* Main Window */
QMainWindow {{
    background-color: {COLORS['background']};
}}

/* Sidebar */
#Sidebar {{
    background-color: {COLORS['sidebar_bg']};
    border-right: none;
    min-width: 220px;
    max-width: 220px;
}}

#Sidebar QLabel {{
    color: {COLORS['sidebar_text']};
    font-size: 13px;
    padding: 8px 16px;
}}

#SidebarTitle {{
    color: #ffffff;
    font-size: 18px;
    font-weight: bold;
    padding: 16px 16px 8px 16px;
}}

#SidebarSubtitle {{
    color: #9aa0a6;
    font-size: 11px;
    padding: 0 16px 16px 16px;
}}

#NavButton {{
    background-color: transparent;
    color: {COLORS['sidebar_text']};
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    text-align: left;
    font-size: 13px;
    margin: 2px 8px;
}}

#NavButton:hover {{
    background-color: {COLORS['sidebar_hover']};
}}

#NavButton:checked {{
    background-color: {COLORS['sidebar_active']};
    color: #ffffff;
    font-weight: bold;
}}

#StatusConnected {{
    color: {COLORS['success']};
    font-size: 12px;
    padding: 8px 16px;
}}

#StatusDisconnected {{
    color: {COLORS['danger']};
    font-size: 12px;
    padding: 8px 16px;
}}

/* Header */
#Header {{
    background-color: {COLORS['header_bg']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 12px 24px;
    min-height: 60px;
    max-height: 60px;
}}

#PageTitle {{
    font-size: 22px;
    font-weight: bold;
    color: {COLORS['text_primary']};
}}

#PageSubtitle {{
    font-size: 13px;
    color: {COLORS['text_secondary']};
}}

/* Content Area */
#ContentArea {{
    background-color: {COLORS['background']};
    border: none;
}}

/* Cards */
#Card {{
    background-color: {COLORS['card_bg']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 16px;
}}

#CardTitle {{
    font-size: 16px;
    font-weight: bold;
    color: {COLORS['text_primary']};
    padding-bottom: 8px;
    border-bottom: 1px solid {COLORS['border_light']};
    margin-bottom: 8px;
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['primary']};
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 13px;
    font-weight: 500;
    min-height: 24px;
}}

QPushButton:hover {{
    background-color: {COLORS['primary_hover']};
}}

QPushButton:pressed {{
    background-color: {COLORS['primary_pressed']};
}}

QPushButton:disabled {{
    background-color: {COLORS['border']};
    color: {COLORS['text_secondary']};
}}

#SecondaryButton {{
    background-color: transparent;
    color: {COLORS['primary']};
    border: 1px solid {COLORS['primary']};
}}

#SecondaryButton:hover {{
    background-color: #e8f0fe;
}}

#DangerButton {{
    background-color: {COLORS['danger']};
}}

#DangerButton:hover {{
    background-color: #d33426;
}}

#SuccessButton {{
    background-color: {COLORS['success']};
}}

#SuccessButton:hover {{
    background-color: #2d9249;
}}

#WarningButton {{
    background-color: {COLORS['warning']};
    color: {COLORS['text_primary']};
}}

#WarningButton:hover {{
    background-color: #e6a800;
}}

/* Input Fields */
QLineEdit {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 20px;
    selection-background-color: {COLORS['primary']};
}}

QLineEdit:focus {{
    border: 2px solid {COLORS['primary']};
    padding: 7px 11px;
}}

QLineEdit:disabled {{
    background-color: {COLORS['surface_variant']};
    color: {COLORS['text_secondary']};
}}

QComboBox {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    min-height: 20px;
}}

QComboBox:focus {{
    border: 2px solid {COLORS['primary']};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {COLORS['text_secondary']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 4px;
    selection-background-color: {COLORS['primary']};
    selection-color: #ffffff;
}}

/* Table */
QTableWidget {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    gridline-color: {COLORS['border_light']};
    selection-background-color: #e8f0fe;
    selection-color: {COLORS['text_primary']};
    font-size: 12px;
}}

QTableWidget::item {{
    padding: 8px;
    border-bottom: 1px solid {COLORS['border_light']};
}}

QTableWidget::item:selected {{
    background-color: #e8f0fe;
}}

QTableWidget::item:hover {{
    background-color: {COLORS['surface_variant']};
}}

QHeaderView::section {{
    background-color: {COLORS['surface_variant']};
    color: {COLORS['text_secondary']};
    border: none;
    border-bottom: 2px solid {COLORS['border']};
    border-right: 1px solid {COLORS['border']};
    padding: 10px 8px;
    font-weight: bold;
    font-size: 12px;
    text-transform: uppercase;
}}

QHeaderView::section:hover {{
    background-color: {COLORS['border']};
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['surface']};
    top: -1px;
}}

QTabBar::tab {{
    background-color: {COLORS['surface_variant']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 20px;
    margin-right: 2px;
    font-size: 13px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['surface']};
    border-bottom: 2px solid {COLORS['primary']};
    font-weight: bold;
}}

QTabBar::tab:hover {{
    background-color: #e8eaed;
}}

/* Scrollbar */
QScrollBar:vertical {{
    background-color: transparent;
    width: 8px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: #c1c1c1;
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #a8a8a8;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 8px;
}}

QScrollBar::handle:horizontal {{
    background-color: #c1c1c1;
    border-radius: 4px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: #a8a8a8;
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* GroupBox */
QGroupBox {{
    font-weight: bold;
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    background-color: {COLORS['surface']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 8px;
    color: {COLORS['text_primary']};
}}

/* Text Edit */
QTextEdit, QPlainTextEdit {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px;
    font-size: 12px;
    font-family: 'Consolas', 'Courier New', monospace;
}}

/* CheckBox */
QCheckBox {{
    spacing: 8px;
    font-size: 13px;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {COLORS['border']};
    background-color: {COLORS['surface']};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS['primary']};
    border-color: {COLORS['primary']};
}}

/* Message Box */
QMessageBox {{
    background-color: {COLORS['surface']};
}}

/* Status Labels */
#StatusLabel {{
    font-size: 12px;
    padding: 4px 8px;
    border-radius: 4px;
}}

#StatusSuccess {{
    background-color: #e6f4ea;
    color: {COLORS['success']};
}}

#StatusError {{
    background-color: #fce8e6;
    color: {COLORS['danger']};
}}

#StatusWarning {{
    background-color: #fef7e0;
    color: #e37400;
}}

#StatusInfo {{
    background-color: #e8f0fe;
    color: {COLORS['info']};
}}

/* Dialog */
QDialog {{
    background-color: {COLORS['surface']};
}}

/* Progress Bar */
QProgressBar {{
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    text-align: center;
    background-color: {COLORS['surface_variant']};
    height: 20px;
}}

QProgressBar::chunk {{
    background-color: {COLORS['primary']};
    border-radius: 5px;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {COLORS['border']};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}
"""
