# 🔐 Active Directory Manager - Freebuff

A comprehensive desktop tool for managing Active Directory without opening the AD Users and Computers console.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Features

### 📊 Dashboard
- Real-time statistics overview
- Total users, computers, groups, and GPOs count
- Quick access to locked, disabled accounts
- Export capabilities

### 👤 User Management
- **Search**: Find users by username, display name, email, department
- **Lock Status Check**: Check if accounts are locked out
- **Reset Password**: Reset user passwords with complexity validation
- **Unlock Account**: Unlock locked user accounts
- **Create User**: Create new users with all attributes
- **Clone User**: Duplicate existing users with group memberships
- **Enable/Disable**: Toggle account status
- **Move User**: Move users between OUs
- **Delete User**: Remove user accounts

### 🏷️ Group Management
- **Search Groups**: Find security and distribution groups
- **Create Groups**: Create new groups with scope and type selection
- **Add/Remove Members**: Manage group memberships
- **View Members**: See all members of a group
- **Delete Groups**: Remove groups

### 🖥️ Computer/Workstation Management
- **List Computers**: View all workstations and servers
- **Check Status**: See enabled/disabled status
- **Enable/Disable Computers**: Toggle computer account status
- **Reset Computer Account**: Reset trust for domain rejoin
- **Move Computers**: Move computers between OUs
- **Delete Computers**: Remove computer accounts

### 📋 Group Policy Management
- **View GPOs**: List all Group Policy Objects
- **Link GPOs**: Link policies to OUs
- **View Details**: See GPO configuration and version info
- **Export GPO Data**: Export GPO information

### 📁 Organizational Units
- **List OUs**: View all OUs in the domain
- **Create OUs**: Create new organizational units
- **View OU Details**: See OU properties

### 📤 Reports & Export
- **Locked Accounts Report**: All currently locked accounts
- **Disabled Accounts Report**: All disabled user accounts
- **Disabled Computers Report**: All disabled computer accounts
- **Never Logged On Report**: Users who have never authenticated
- **Password Expired Report**: Users with expired passwords
- **CSV Export**: Export any report to CSV format

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- Network access to Active Directory domain controller
- Domain user account with appropriate permissions

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the Application
```bash
python main.py
```

## 📦 Standalone .exe (no Python needed)

IT staff can run AD Manager without installing Python via a packaged Windows build.

### Use the prebuilt app
1. Copy the **whole `dist/AD-Manager/` folder** to the target machine (all support files are required, not just the .exe).
2. Run `AD-Manager.exe`.
3. Logs are written to `%LOCALAPPDATA%\AD-Manager\ad_manager.log`.

### Build it yourself
```bash
pip install pyinstaller
build-exe.bat        # or: pyinstaller AD-Manager.spec --noconfirm --clean
```
The build output lands in `dist/AD-Manager/`.

> **Notes**
> - The build machine should run the same Windows bitness/OS family you target (build on Windows for a Windows exe).
> - SmartScreen may warn on unsigned exes from unknown publishers — click *More info → Run anyway*, or sign the binary with your organization's code-signing certificate.
> - The packaged app still needs network access to your domain controllers; it ships with no domain data.

## 📖 Usage Guide

### 1. Connecting to Active Directory

1. Launch the application
2. Click **"Connect to AD"** in the sidebar
3. Enter connection details:
   - **Domain**: Your AD domain (e.g., `corp.example.com`)
   - **Username**: Your domain username
   - **Password**: Your password
4. Click **"Test Connection"** to verify
5. Click **"Connect"** to proceed

### 2. Dashboard

The dashboard provides an overview of your AD environment:
- Total users, computers, groups, and GPOs
- Quick counts of enabled, disabled, and locked accounts
- Click on any card to jump to the detailed report

### 3. User Management

**Searching Users:**
1. Go to **Users** in the sidebar
2. Use the search bar to filter by username, name, email, etc.
3. Check "Enabled only" or "Locked only" for quick filters

**Resetting Passwords:**
1. Select a user from the table
2. Right-click and select "Reset Password" or use the Actions tab
3. Enter and confirm the new password
4. Choose if user must change password at next logon

**Checking Lock Status:**
1. Select a user
2. The "Locked" column shows 🔒 Yes or 🔓 No
3. Use the "Locked only" checkbox to filter all locked accounts

**Creating New Users:**
1. Click "➕ Create User" button
2. Fill in required fields (username, name, password)
3. Select the target OU
4. Click "Create User"

**Cloning Users:**
1. Right-click on the source user
2. Select "Clone User"
3. Enter new user details
4. Choose whether to copy group memberships
5. Click "Clone User"

### 4. Group Management

**Creating Groups:**
1. Go to **Groups** in the sidebar
2. Click "➕ Create Group"
3. Enter group name, description, scope, and type
4. Select target OU
5. Click "Create Group"

**Adding Members:**
1. Select a group
2. Go to the "⚡ Actions" tab
3. Enter username and click "➕ Add"

### 5. Computer Management

**Workstation Operations:**
1. Go to **Computers** in the sidebar
2. Search for computers by name
3. Right-click for context menu options:
   - Enable/Disable
   - Reset Account (for domain rejoin)
   - Move to OU
   - Delete

### 6. Group Policy Management

**Linking GPOs:**
1. Go to **Group Policy** in the sidebar
2. Select a GPO
3. Click "🔗 Link GPO to OU"
4. Select the target OU
5. Click "Link GPO"

### 7. Exporting Data

1. Go to **Dashboard** → **📤 Export** tab
2. Select the data type to export:
   - Users
   - Computers
   - Groups
   - GPOs
3. Choose save location
4. Data is exported to CSV format

## 🔐 Permissions Required

The domain account used must have the following permissions:
- **Read** access to AD objects
- **Reset Password** for password changes
- **Modify** attributes for user/computer updates
- **Create/Delete** for creating new objects
- **Group Management** for adding/removing members

## 📁 Project Structure

```
.
├── main.py                      # Application entry point
├── requirements.txt             # Python dependencies
├── README.md                    # Documentation
├── core/
│   ├── __init__.py
│   └── ad_connection.py         # AD connection and operations
├── ui/
│   ├── __init__.py
│   ├── main_window.py           # Main window with navigation
│   ├── login_dialog.py          # Connection dialog
│   ├── user_management.py       # User management panel
│   ├── group_management.py      # Group management panel
│   ├── computer_management.py   # Computer management panel
│   ├── policy_management.py     # GPO management panel
│   ├── ou_management.py         # OU management panel
│   ├── reports_panel.py         # Dashboard and reports
│   ├── styles.py                # UI styling
│   └── widgets.py               # Custom widgets
└── utils/
    ├── __init__.py
    └── helpers.py               # Utility functions
```

## 🛠️ Troubleshooting

### Connection Issues
- Ensure you can reach the domain controller
- Check if LDAPS (port 636) is enabled
- Try port 389 with SSL disabled
- Verify domain name format (e.g., `corp.example.com`)

### Authentication Errors
- Verify username format: `DOMAIN\username` or `username@domain.com`
- Ensure password is correct
- Check if account is locked or disabled

### Permission Denied
- Contact your AD administrator
- Ensure the account has necessary permissions

## 📝 License

This project is open source and available for use.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or issues.

---

**Built with ❤️ by Freebuff**
