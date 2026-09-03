#!/usr/bin/env python3
"""
Active Directory Manager - Freebuff
A comprehensive tool for managing Active Directory
without opening AD Users and Computers.

Features:
- Dashboard with overview statistics
- User Management (search, lock check, reset, create, clone)
- Group Management (create, add/remove members)
- Computer/Workstation Management
- Group Policy Management
- OU Management
- Reports and CSV Export

Requirements:
- Python 3.8+
- PyQt6
- ldap3

Usage:
    python main.py
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ad_manager.log'),
        logging.StreamHandler(sys.stdout),
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the AD Manager application."""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QFont, QPalette, QColor

        # High DPI support
        os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'

        app = QApplication(sys.argv)
        app.setApplicationName("AD Manager")
        app.setOrganizationName("Freebuff")
        app.setApplicationVersion("1.0.0")

        # Set default font
        font = QFont("Segoe UI", 10)
        app.setFont(font)

        # Create and show main window
        from ui.main_window import MainWindow

        window = MainWindow()
        window.show()

        logger.info("AD Manager started successfully")

        sys.exit(app.exec())

    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        print(f"\n❌ Missing dependency: {e}")
        print("\nPlease install required packages:")
        print("  pip install PyQt6 ldap3")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        print(f"\n❌ Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
