"""
Active Directory Connection Manager
Handles LDAP connection to Active Directory domain controllers.
"""

import ssl
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from ldap3 import Server, Connection, ALL, SUBTREE, BASE, LEVEL
from ldap3.core.exceptions import (
    LDAPBindError,
    LDAPSocketOpenError,
    LDAPAttributeError,
    LDAPException,
)

logger = logging.getLogger(__name__)


@dataclass
class ADConfig:
    """Active Directory connection configuration."""
    server: str = ""
    port: int = 636
    use_ssl: bool = True
    domain: str = ""
    base_dn: str = ""
    username: str = ""
    password: str = ""
    timeout: int = 30
    auto_discover: bool = True


@dataclass
class ADUserInfo:
    """User information from Active Directory."""
    dn: str = ""
    sam_account_name: str = ""
    display_name: str = ""
    given_name: str = ""
    sn: str = ""
    email: str = ""
    office: str = ""
    department: str = ""
    title: str = ""
    telephone: str = ""
    mobile: str = ""
    manager: str = ""
    member_of: List[str] = field(default_factory=list)
    enabled: bool = True
    locked_out: bool = False
    password_expired: bool = False
    must_change_password: bool = False
    last_logon: Optional[datetime] = None
    password_last_set: Optional[datetime] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    description: str = ""
    path: str = ""
    sid: str = ""
    when_created: str = ""
    when_changed: str = ""
    logon_count: int = 0
    bad_password_count: int = 0
    home_drive: str = ""
    home_directory: str = ""
    script_path: str = ""
    profile_path: str = ""
    distinguished_name: str = ""


@dataclass
class ADComputerInfo:
    """Computer/Workstation information from Active Directory."""
    dn: str = ""
    name: str = ""
    sam_account_name: str = ""
    operating_system: str = ""
    description: str = ""
    enabled: bool = True
    last_logon: Optional[datetime] = None
    password_last_set: Optional[datetime] = None
    when_created: str = ""
    when_changed: str = ""
    distinguished_name: str = ""
    dns_host_name: str = ""
    location: str = ""
    managed_by: str = ""
    member_of: List[str] = field(default_factory=list)
    sid: str = ""


@dataclass
class ADGroupInfo:
    """Group information from Active Directory."""
    dn: str = ""
    name: str = ""
    sam_account_name: str = ""
    description: str = ""
    group_scope: str = "Global"
    group_type: str = "Security"
    members: List[str] = field(default_factory=list)
    member_count: int = 0
    when_created: str = ""
    when_changed: str = ""
    distinguished_name: str = ""
    managed_by: str = ""
    email: str = ""


@dataclass
class ADGPOInfo:
    """Group Policy Object information."""
    dn: str = ""
    name: str = ""
    display_name: str = ""
    description: str = ""
    when_created: str = ""
    when_changed: str = ""
    distinguished_name: str = ""
    flags: int = 0
    gpc_file_system_path: str = ""
    version: int = 0
    is_user_policy: bool = True
    is_computer_policy: bool = True


@dataclass
class ADOUInfo:
    """Organizational Unit information."""
    dn: str = ""
    name: str = ""
    description: str = ""
    when_created: str = ""
    when_changed: str = ""
    distinguished_name: str = ""


class ADConnection:
    """Manages connection and operations with Active Directory."""

    # Common user attributes
    USER_ATTRIBUTES = [
        'sAMAccountName', 'displayName', 'givenName', 'sn', 'mail',
        'physicalDeliveryOfficeName', 'department', 'title',
        'telephoneNumber', 'mobile', 'manager', 'memberOf',
        'userAccountControl', 'lockoutTime', 'pwdLastSet',
        'lastLogonTimestamp', 'whenCreated', 'whenChanged',
        'description', 'distinguishedName', 'objectSid',
        'logonCount', 'badPwdCount', 'homeDrive', 'homeDirectory',
        'scriptPath', 'profilePath', 'userPrincipalName',
        'objectGUID', 'primaryGroupID',
    ]

    COMPUTER_ATTRIBUTES = [
        'sAMAccountName', 'name', 'operatingSystem',
        'operatingSystemVersion', 'description', 'userAccountControl',
        'lastLogonTimestamp', 'pwdLastSet', 'whenCreated', 'whenChanged',
        'distinguishedName', 'dnsHostName', 'location', 'managedBy',
        'memberOf', 'objectSid', 'cn',
    ]

    GROUP_ATTRIBUTES = [
        'sAMAccountName', 'name', 'description', 'groupType',
        'member', 'whenCreated', 'whenChanged',
        'distinguishedName', 'managedBy', 'mail', 'cn',
    ]

    GPO_ATTRIBUTES = [
        'displayName', 'name', 'description', 'flags',
        'gPCFileSysPath', 'versionNumber', 'machineExtensionNames',
        'userExtensionNames', 'whenCreated', 'whenChanged',
        'distinguishedName',
    ]

    def __init__(self):
        self.connection: Optional[Connection] = None
        self.server: Optional[Server] = None
        self.config: Optional[ADConfig] = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected and self.connection is not None and self.connection.bound

    def connect(self, config: ADConfig) -> Tuple[bool, str]:
        """
        Establish connection to Active Directory.
        Returns (success, message).
        """
        try:
            self.config = config

            # Build server URI
            if config.auto_discover and config.domain:
                server_uri = config.domain
            elif config.server:
                server_uri = config.server
            else:
                return False, "No server or domain specified."

            # Create server
            tls_config = None
            if config.use_ssl:
                tls_config = ssl.create_default_context()
                tls_config.check_hostname = False
                tls_config.verify_mode = ssl.CERT_NONE

            self.server = Server(
                server_uri,
                port=config.port,
                use_ssl=config.use_ssl,
                get_info=ALL,
                tls=tls_config,
                connect_timeout=config.timeout,
            )

            # Format username with domain
            username = config.username
            if config.domain and '\\' not in username and '@' not in username:
                username = f"{config.domain}\\{username}"

            # Connect
            self.connection = Connection(
                self.server,
                user=username,
                password=config.password,
                auto_bind=True,
                receive_timeout=config.timeout,
            )

            # Get base DN if not specified
            if not config.base_dn and self.server.info:
                naming_contexts = self.server.info.naming_contexts
                if naming_contexts:
                    config.base_dn = naming_contexts[0]

            self._connected = True
            logger.info(f"Connected to AD server: {server_uri}")

            return True, f"Successfully connected to {server_uri}"

        except LDAPBindError as e:
            self._connected = False
            error_msg = f"Authentication failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except LDAPSocketOpenError as e:
            self._connected = False
            error_msg = f"Cannot connect to server: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except LDAPException as e:
            self._connected = False
            error_msg = f"LDAP error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            self._connected = False
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def disconnect(self):
        """Close the AD connection."""
        try:
            if self.connection and self.connection.bound:
                self.connection.unbind()
        except Exception:
            pass
        self._connected = False
        self.connection = None

    def search(
        self,
        search_filter: str,
        attributes: List[str] = None,
        search_base: str = None,
        search_scope: int = SUBTREE,
        size_limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Search Active Directory.
        Returns list of dictionaries with attribute values.
        """
        if not self.is_connected:
            raise ConnectionError("Not connected to Active Directory")

        search_base = search_base or self.config.base_dn
        attributes = attributes or ['*']

        try:
            self.connection.search(
                search_base=search_base,
                search_filter=search_filter,
                attributes=attributes,
                search_scope=search_scope,
                size_limit=size_limit,
                paged_size=500,
            )

            results = []
            for entry in self.connection.entries:
                entry_dict = {}
                for attr in entry:
                    value = entry[attr].value
                    # Convert lists to proper format
                    if isinstance(value, list) and len(value) == 1:
                        value = value[0]
                    entry_dict[attr.key] = value
                entry_dict['_raw_entry'] = entry
                results.append(entry_dict)

            return results

        except LDAPException as e:
            logger.error(f"Search error: {str(e)}")
            raise

    def get_all_ous(self) -> List[ADOUInfo]:
        """Get all Organizational Units."""
        results = self.search(
            "(objectClass=organizationalUnit)",
            ['ou', 'description', 'whenCreated', 'whenChanged', 'distinguishedName'],
        )

        ous = []
        for r in results:
            ou = ADOUInfo(
                dn=r.get('distinguishedName', ''),
                name=r.get('ou', ''),
                description=r.get('description', ''),
                when_created=str(r.get('whenCreated', '')),
                when_changed=str(r.get('whenChanged', '')),
                distinguished_name=r.get('distinguishedName', ''),
            )
            ous.append(ou)

        return sorted(ous, key=lambda x: x.name)

    def search_users(
        self,
        query: str = "*",
        search_field: str = "sAMAccountName",
        enabled_only: bool = False,
        size_limit: int = 500,
    ) -> List[ADUserInfo]:
        """Search for users in Active Directory."""
        search_filter = f"(&(objectClass=user)(objectCategory=person)({search_field}={query}))"
        if enabled_only:
            # UAC flag 0x2 is ACCOUNTDISABLE
            search_filter = f"(&(objectClass=user)(objectCategory=person)({search_field}={query})(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"

        results = self.search(
            search_filter,
            self.USER_ATTRIBUTES,
            size_limit=size_limit,
        )

        return [self._dict_to_user(r) for r in results]

    def get_user(self, sam_account_name: str) -> Optional[ADUserInfo]:
        """Get a single user by sAMAccountName."""
        results = self.search_users(sam_account_name, "sAMAccountName")
        return results[0] if results else None

    def get_user_by_dn(self, dn: str) -> Optional[ADUserInfo]:
        """Get a single user by Distinguished Name."""
        results = self.search(
            f"(distinguishedName={dn})",
            self.USER_ATTRIBUTES,
            size_limit=1,
        )
        return self._dict_to_user(results[0]) if results else None

    def search_computers(
        self,
        query: str = "*",
        search_field: str = "name",
        enabled_only: bool = False,
        size_limit: int = 500,
    ) -> List[ADComputerInfo]:
        """Search for computers/workstations."""
        search_filter = f"(&(objectClass=computer)({search_field}={query}))"
        if enabled_only:
            search_filter = f"(&(objectClass=computer)({search_field}={query})(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"

        results = self.search(
            search_filter,
            self.COMPUTER_ATTRIBUTES,
            size_limit=size_limit,
        )

        return [self._dict_to_computer(r) for r in results]

    def get_computer(self, name: str) -> Optional[ADComputerInfo]:
        """Get a single computer by name."""
        results = self.search_computers(name, "name")
        return results[0] if results else None

    def search_groups(
        self,
        query: str = "*",
        search_field: str = "sAMAccountName",
        size_limit: int = 500,
    ) -> List[ADGroupInfo]:
        """Search for groups."""
        search_filter = f"(&(objectClass=group)({search_field}={query}))"

        results = self.search(
            search_filter,
            self.GROUP_ATTRIBUTES,
            size_limit=size_limit,
        )

        return [self._dict_to_group(r) for r in results]

    def get_group(self, sam_account_name: str) -> Optional[ADGroupInfo]:
        """Get a single group by sAMAccountName."""
        results = self.search_groups(sam_account_name, "sAMAccountName")
        return results[0] if results else None

    def search_gpos(
        self,
        query: str = "*",
        size_limit: int = 500,
    ) -> List[ADGPOInfo]:
        """Search for Group Policy Objects."""
        # GPOs are stored in CN=Policies,CN=System
        search_base = f"CN=Policies,CN=System,{self.config.base_dn}"
        search_filter = f"(displayName={query})"

        results = self.search(
            search_filter,
            self.GPO_ATTRIBUTES,
            search_base=search_base,
            size_limit=size_limit,
        )

        return [self._dict_to_gpo(r) for r in results]

    def get_all_gpos(self) -> List[ADGPOInfo]:
        """Get all Group Policy Objects."""
        return self.search_gpos("*")

    # ─── User Operations ──────────────────────────────────────────────

    def check_user_locked(self, sam_account_name: str) -> Tuple[bool, bool, str]:
        """
        Check if a user account is locked out.
        Returns (exists, is_locked, message).
        """
        user = self.get_user(sam_account_name)
        if not user:
            return False, False, f"User '{sam_account_name}' not found."

        return True, user.locked_out, (
            f"User '{sam_account_name}' is {'LOCKED' if user.locked_out else 'not locked'}."
        )

    def unlock_user(self, sam_account_name: str) -> Tuple[bool, str]:
        """Unlock a user account."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        try:
            user = self.get_user(sam_account_name)
            if not user:
                return False, f"User '{sam_account_name}' not found."

            # Clear lockoutTime by setting it to 0
            self.connection.modify(
                user.dn,
                {'lockoutTime': [('MODIFY_REPLACE', [0])]}
            )

            if self.connection.result['result'] == 0:
                return True, f"User '{sam_account_name}' has been unlocked successfully."
            else:
                return False, f"Failed to unlock: {self.connection.result['message']}"

        except Exception as e:
            return False, f"Error unlocking user: {str(e)}"

    def reset_password(
        self,
        sam_account_name: str,
        new_password: str,
        must_change: bool = True,
    ) -> Tuple[bool, str]:
        """Reset a user's password."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        try:
            user = self.get_user(sam_account_name)
            if not user:
                return False, f"User '{sam_account_name}' not found."

            # Encode password for LDAP
            new_password_encoded = f'"{new_password}"'.encode('utf-16-le')
            unicode_pwd = new_password_encoded

            # Reset password
            changes = {
                'unicodePwd': [('DELETE_REPLACE', [unicode_pwd])],
            }

            # If must change password at next logon
            if must_change:
                changes['pwdLastSet'] = [('MODIFY_REPLACE', [0])]

            self.connection.modify(user.dn, changes)

            if self.connection.result['result'] == 0:
                msg = f"Password reset for '{sam_account_name}' successfully."
                if must_change:
                    msg += " User must change password at next logon."
                return True, msg
            else:
                return False, f"Failed to reset password: {self.connection.result['message']}"

        except Exception as e:
            return False, f"Error resetting password: {str(e)}"

    def enable_user(self, sam_account_name: str) -> Tuple[bool, str]:
        """Enable a user account."""
        return self._set_user_account_disabled(sam_account_name, False)

    def disable_user(self, sam_account_name: str) -> Tuple[bool, str]:
        """Disable a user account."""
        return self._set_user_account_disabled(sam_account_name, True)

    def _set_user_account_disabled(
        self, sam_account_name: str, disabled: bool
    ) -> Tuple[bool, str]:
        """Enable or disable a user account."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        try:
            user = self.get_user(sam_account_name)
            if not user:
                return False, f"User '{sam_account_name}' not found."

            # Get current UAC value
            uac = user.enabled
            # ACCOUNTDISABLE flag = 0x2
            current_uac = 512  # Normal user default
            if user.locked_out:
                current_uac |= 0x10  # LOCKOUT

            if disabled:
                new_uac = current_uac | 0x2  # Set ACCOUNTDISABLE
            else:
                new_uac = current_uac & ~0x2  # Clear ACCOUNTDISABLE

            self.connection.modify(
                user.dn,
                {'userAccountControl': [('MODIFY_REPLACE', [new_uac])]}
            )

            if self.connection.result['result'] == 0:
                action = "disabled" if disabled else "enabled"
                return True, f"User '{sam_account_name}' has been {action}."
            else:
                return False, f"Failed: {self.connection.result['message']}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def create_user(
        self,
        ou_dn: str,
        sam_account_name: str,
        first_name: str,
        last_name: str,
        password: str,
        email: str = "",
        display_name: str = "",
        department: str = "",
        title: str = "",
        description: str = "",
        must_change_password: bool = True,
    ) -> Tuple[bool, str]:
        """Create a new user in the specified OU."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        if not display_name:
            display_name = f"{first_name} {last_name}"

        user_dn = f"CN={sam_account_name},{ou_dn}"

        attributes = {
            'objectClass': ['top', 'person', 'organizationalPerson', 'user'],
            'sAMAccountName': sam_account_name,
            'givenName': first_name,
            'sn': last_name,
            'displayName': display_name,
            'userPrincipalName': f"{sam_account_name}@{self.config.domain}",
            'userAccountControl': 0x200,  # NORMAL_ACCOUNT
        }

        if email:
            attributes['mail'] = email
        if department:
            attributes['department'] = department
        if title:
            attributes['title'] = title
        if description:
            attributes['description'] = description

        try:
            # Add user
            self.connection.add(
                user_dn,
                ['top', 'person', 'organizationalPerson', 'user'],
                attributes,
            )

            if self.connection.result['result'] != 0:
                return False, f"Failed to create user: {self.connection.result['message']}"

            # Set password
            password_encoded = f'"{password}"'.encode('utf-16-le')
            self.connection.modify(
                user_dn,
                {'unicodePwd': [('ADD', [password_encoded])]},
            )

            if self.connection.result['result'] != 0:
                # Try to clean up
                self.connection.delete(user_dn)
                return False, f"Failed to set password: {self.connection.result['message']}"

            # Enable account
            self.connection.modify(
                user_dn,
                {'userAccountControl': [('MODIFY_REPLACE', [512])]},
            )

            # Set must change password
            if must_change_password:
                self.connection.modify(
                    user_dn,
                    {'pwdLastSet': [('MODIFY_REPLACE', [0])]},
                )

            return True, f"User '{sam_account_name}' created successfully in {ou_dn}"

        except Exception as e:
            return False, f"Error creating user: {str(e)}"

    def clone_user(
        self,
        source_sam: str,
        new_sam: str,
        new_first_name: str,
        new_last_name: str,
        new_password: str,
        ou_dn: str = None,
        copy_group_membership: bool = True,
    ) -> Tuple[bool, str]:
        """
        Clone a user, copying attributes from source to new user.
        """
        source = self.get_user(source_sam)
        if not source:
            return False, f"Source user '{source_sam}' not found."

        target_dn = ou_dn or self._get_dn_parent(source.dn)

        # Create user with source attributes
        success, msg = self.create_user(
            ou_dn=target_dn,
            sam_account_name=new_sam,
            first_name=new_first_name,
            last_name=new_last_name,
            password=new_password,
            email="",
            display_name=f"{new_first_name} {new_last_name}",
            department=source.department,
            title=source.title,
            description=f"Cloned from {source_sam}: {source.description}" if source.description else f"Cloned from {source_sam}",
        )

        if not success:
            return False, msg

        new_user = self.get_user(new_sam)
        if not new_user:
            return True, msg + " (Warning: could not verify user creation)"

        # Copy additional attributes
        try:
            modifications = {}
            if source.office:
                modifications['physicalDeliveryOfficeName'] = [('MODIFY_REPLACE', [source.office])]
            if source.telephone:
                modifications['telephoneNumber'] = [('MODIFY_REPLACE', [source.telephone])]
            if source.mobile:
                modifications['mobile'] = [('MODIFY_REPLACE', [source.mobile])]
            if source.home_drive:
                modifications['homeDrive'] = [('MODIFY_REPLACE', [source.home_drive])]
            if source.home_directory:
                modifications['homeDirectory'] = [('MODIFY_REPLACE', [source.home_directory])]
            if source.script_path:
                modifications['scriptPath'] = [('MODIFY_REPLACE', [source.script_path])]
            if source.profile_path:
                modifications['profilePath'] = [('MODIFY_REPLACE', [source.profile_path])]

            if modifications:
                self.connection.modify(new_user.dn, modifications)
        except Exception as e:
            logger.warning(f"Could not copy some attributes: {e}")

        # Copy group memberships
        if copy_group_membership and source.member_of:
            groups_added = []
            for group_dn in source.member_of:
                try:
                    self.connection.modify(
                        group_dn,
                        {'member': [('ADD', [new_user.dn])]},
                    )
                    groups_added.append(group_dn.split(',')[0].replace('CN=', ''))
                except Exception as e:
                    logger.warning(f"Could not add to group {group_dn}: {e}")

            if groups_added:
                msg += f" Added to groups: {', '.join(groups_added)}"

        return True, msg

    def move_user(self, user_sam: str, target_ou_dn: str) -> Tuple[bool, str]:
        """Move a user to a different OU."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        user = self.get_user(user_sam)
        if not user:
            return False, f"User '{user_sam}' not found."

        try:
            new_dn = f"CN={user_sam},{target_ou_dn}"
            self.connection.modify_dn(user.dn, f"CN={user_sam}", new_superior=target_ou_dn)

            if self.connection.result['result'] == 0:
                return True, f"User '{user_sam}' moved to {target_ou_dn}"
            else:
                return False, f"Failed to move: {self.connection.result['message']}"

        except Exception as e:
            return False, f"Error moving user: {str(e)}"

    def set_user_attribute(
        self, sam_account_name: str, attribute: str, value: Any
    ) -> Tuple[bool, str]:
        """Set a single user attribute."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        user = self.get_user(sam_account_name)
        if not user:
            return False, f"User '{sam_account_name}' not found."

        try:
            self.connection.modify(
                user.dn,
                {attribute: [('MODIFY_REPLACE', [value])]},
            )

            if self.connection.result['result'] == 0:
                return True, f"Attribute '{attribute}' updated for '{sam_account_name}'."
            else:
                return False, f"Failed: {self.connection.result['message']}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def delete_user(self, sam_account_name: str) -> Tuple[bool, str]:
        """Delete a user account."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        user = self.get_user(sam_account_name)
        if not user:
            return False, f"User '{sam_account_name}' not found."

        try:
            self.connection.delete(user.dn)

            if self.connection.result['result'] == 0:
                return True, f"User '{sam_account_name}' deleted successfully."
            else:
                return False, f"Failed to delete: {self.connection.result['message']}"

        except Exception as e:
            return False, f"Error deleting user: {str(e)}"

    # ─── Group Operations ─────────────────────────────────────────────

    def create_group(
        self,
        ou_dn: str,
        name: str,
        description: str = "",
        scope: str = "Global",
        group_type: str = "Security",
    ) -> Tuple[bool, str]:
        """Create a new group."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        group_dn = f"CN={name},{ou_dn}"

        # Determine group type flag
        # 0x80000000 = GROUP_TYPE_SECURITY_ACCOUNT
        # 0x00000002 = GROUP_GLOBAL
        # 0x00000004 = GROUP_DOMAIN_LOCAL
        # 0x00000008 = GROUP_UNIVERSAL
        scope_flags = {"Global": 0x2, "DomainLocal": 0x4, "Universal": 0x8}
        type_flags = {"Security": 0x80000000, "Distribution": 0x0}

        group_type_value = scope_flags.get(scope, 0x2) | type_flags.get(group_type, 0x80000000)

        attributes = {
            'sAMAccountName': name,
            'displayName': name,
            'groupType': group_type_value,
        }
        if description:
            attributes['description'] = description

        try:
            self.connection.add(
                group_dn,
                ['top', 'group'],
                attributes,
            )

            if self.connection.result['result'] == 0:
                return True, f"Group '{name}' created successfully."
            else:
                return False, f"Failed: {self.connection.result['message']}"

        except Exception as e:
            return False, f"Error creating group: {str(e)}"

    def add_user_to_group(
        self, user_sam: str, group_sam: str
    ) -> Tuple[bool, str]:
        """Add a user to a group."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        user = self.get_user(user_sam)
        if not user:
            return False, f"User '{user_sam}' not found."

        group = self.get_group(group_sam)
        if not group:
            return False, f"Group '{group_sam}' not found."

        try:
            self.connection.modify(
                group.dn,
                {'member': [('ADD', [user.dn])]},
            )

            if self.connection.result['result'] == 0:
                return True, f"User '{user_sam}' added to group '{group_sam}'."
            else:
                return False, f"Failed: {self.connection.result['message']}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def remove_user_from_group(
        self, user_sam: str, group_sam: str
    ) -> Tuple[bool, str]:
        """Remove a user from a group."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        user = self.get_user(user_sam)
        if not user:
            return False, f"User '{user_sam}' not found."

        group = self.get_group(group_sam)
        if not group:
            return False, f"Group '{group_sam}' not found."

        try:
            self.connection.modify(
                group.dn,
                {'member': [('REMOVE', [user.dn])]},
            )

            if self.connection.result['result'] == 0:
                return True, f"User '{user_sam}' removed from group '{group_sam}'."
            else:
                return False, f"Failed: {self.connection.result['message']}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def get_group_members(self, group_sam: str) -> List[str]:
        """Get list of member DNs in a group."""
        group = self.get_group(group_sam)
        if not group:
            return []
        return group.members

    def delete_group(self, group_sam: str) -> Tuple[bool, str]:
        """Delete a group."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        group = self.get_group(group_sam)
        if not group:
            return False, f"Group '{group_sam}' not found."

        try:
            self.connection.delete(group.dn)
            if self.connection.result['result'] == 0:
                return True, f"Group '{group_sam}' deleted."
            else:
                return False, f"Failed: {self.connection.result['message']}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    # ─── Computer Operations ──────────────────────────────────────────

    def enable_computer(self, name: str) -> Tuple[bool, str]:
        """Enable a computer account."""
        return self._set_computer_disabled(name, False)

    def disable_computer(self, name: str) -> Tuple[bool, str]:
        """Disable a computer account."""
        return self._set_computer_disabled(name, True)

    def _set_computer_disabled(
        self, name: str, disabled: bool
    ) -> Tuple[bool, str]:
        """Enable or disable a computer account."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        computer = self.get_computer(name)
        if not computer:
            return False, f"Computer '{name}' not found."

        try:
            current_uac = 4096  # WORKSTATION_TRUST_ACCOUNT
            if disabled:
                new_uac = current_uac | 0x2
            else:
                new_uac = current_uac & ~0x2

            self.connection.modify(
                computer.dn,
                {'userAccountControl': [('MODIFY_REPLACE', [new_uac])]},
            )

            if self.connection.result['result'] == 0:
                action = "disabled" if disabled else "enabled"
                return True, f"Computer '{name}' has been {action}."
            else:
                return False, f"Failed: {self.connection.result['message']}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def reset_computer_password(self, name: str) -> Tuple[bool, str]:
        """Reset computer account password (rejoin)."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        computer = self.get_computer(name)
        if not computer:
            return False, f"Computer '{name}' not found."

        try:
            # Generate a random password
            import secrets
            import string
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            new_password = ''.join(secrets.choice(chars) for _ in range(24))

            password_encoded = f'"{new_password}"'.encode('utf-16-le')

            self.connection.modify(
                computer.dn,
                {'unicodePwd': [('DELETE_REPLACE', [password_encoded])]},
            )

            if self.connection.result['result'] == 0:
                return True, f"Computer '{name}' password reset. Reset the trust account in AD Users and Computers."
            else:
                return False, f"Failed: {self.connection.result['message']}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def move_computer(self, computer_name: str, target_ou_dn: str) -> Tuple[bool, str]:
        """Move a computer to a different OU."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        computer = self.get_computer(computer_name)
        if not computer:
            return False, f"Computer '{computer_name}' not found."

        try:
            self.connection.modify_dn(
                computer.dn, f"CN={computer_name}", new_superior=target_ou_dn
            )

            if self.connection.result['result'] == 0:
                return True, f"Computer '{computer_name}' moved to {target_ou_dn}"
            else:
                return False, f"Failed: {self.connection.result['message']}"

        except Exception as e:
            return False, f"Error: {str(e)}"

    def delete_computer(self, name: str) -> Tuple[bool, str]:
        """Delete a computer account."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        computer = self.get_computer(name)
        if not computer:
            return False, f"Computer '{name}' not found."

        try:
            self.connection.delete(computer.dn)
            if self.connection.result['result'] == 0:
                return True, f"Computer '{name}' deleted."
            else:
                return False, f"Failed: {self.connection.result['message']}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    # ─── GPO Operations ───────────────────────────────────────────────

    def get_linked_gpos(self, dn: str) -> List[ADGPOInfo]:
        """Get GPOs linked to an OU or container."""
        results = self.search(
            f"(distinguishedName={dn})",
            ['gPLink', 'gPOptions'],
        )

        gpos = []
        if results and 'gPLink' in results[0]:
            gplink = results[0]['gPLink']
            if gplink:
                # Parse gPLink string
                import re
                links = re.findall(r'\[LDAP://cn=([^,]+),.*?;', str(gplink))
                gpo_names = links

                for gpo_name in gpo_names:
                    # Search for GPO details
                    gpo_results = self.search_gpos(gpo_name)
                    gpos.extend(gpo_results)

        return gpos

    def link_gpo_to_ou(
        self, gpo_dn: str, ou_dn: str
    ) -> Tuple[bool, str]:
        """Link a GPO to an OU."""
        if not self.is_connected:
            return False, "Not connected to Active Directory."

        try:
            gplink_value = f"[LDAP://{gpo_dn};0]"

            # Check if gPLink already exists
            self.connection.search(
                ou_dn,
                '(objectClass=*)',
                attributes=['gPLink', 'gPOptions'],
            )

            if self.connection.entries:
                entry = self.connection.entries[0]
                existing_gplink = str(entry.gPLink.value) if entry.gPLink.value else ""

                if gpo_dn.lower() in existing_gplink.lower():
                    return False, "GPO is already linked to this OU."

                new_gplink = f"{existing_gplink}{gplink_value}" if existing_gplink else gplink_value

                self.connection.modify(
                    ou_dn,
                    {'gPLink': [('MODIFY_REPLACE', [new_gplink])]},
                )
            else:
                self.connection.modify(
                    ou_dn,
                    {'gPLink': [('MODIFY_REPLACE', [gplink_value])]},
                )

            if self.connection.result['result'] == 0:
                return True, "GPO linked successfully."
            else:
                return False, f"Failed: {self.connection.result['message']}"

        except Exception as e:
            return False, f"Error linking GPO: {str(e)}"

    # ─── Reports ──────────────────────────────────────────────────────

    def get_locked_accounts(self) -> List[ADUserInfo]:
        """Get all locked accounts."""
        results = self.search(
            "(&(objectClass=user)(objectCategory=person)(lockoutTime>=1))",
            self.USER_ATTRIBUTES,
        )
        return [self._dict_to_user(r) for r in results]

    def get_disabled_accounts(self) -> List[ADUserInfo]:
        """Get all disabled user accounts."""
        results = self.search(
            "(&(objectClass=user)(objectCategory=person)(userAccountControl:1.2.840.113556.1.4.803:=2))",
            self.USER_ATTRIBUTES,
        )
        return [self._dict_to_user(r) for r in results]

    def get_password_expired_users(self) -> List[ADUserInfo]:
        """Get users whose password has expired."""
        results = self.search(
            "(&(objectClass=user)(objectCategory=person)(userAccountControl:1.2.840.113556.1.4.803:=8388608))",
            self.USER_ATTRIBUTES,
        )
        return [self._dict_to_user(r) for r in results]

    def get_never_logged_on(self) -> List[ADUserInfo]:
        """Get users who have never logged on."""
        results = self.search(
            "(&(objectClass=user)(objectCategory=person)(!(userAccountControl:1.2.840.113556.1.4.803:=2))(|(lastLogonTimestamp=0)(!(lastLogonTimestamp=*))))",
            self.USER_ATTRIBUTES,
            size_limit=500,
        )
        return [self._dict_to_user(r) for r in results]

    def get_disabled_computers(self) -> List[ADComputerInfo]:
        """Get all disabled computer accounts."""
        results = self.search(
            "(&(objectClass=computer)(userAccountControl:1.2.840.113556.1.4.803:=2))",
            self.COMPUTER_ATTRIBUTES,
        )
        return [self._dict_to_computer(r) for r in results]

    def get_domain_info(self) -> Dict[str, Any]:
        """Get basic domain information."""
        info = {}
        try:
            if self.server and self.server.info:
                info['naming_contexts'] = self.server.info.naming_contexts
                info['supported_controls'] = self.server.info.supported_controls
                info['server_name'] = self.server.info.other.get('serverName', [''])[0]
                info['domain_name'] = self.config.domain if self.config else ''
                info['base_dn'] = self.config.base_dn if self.config else ''
        except Exception:
            pass
        return info

    # ─── Helper Methods ───────────────────────────────────────────────

    def _dict_to_user(self, data: Dict[str, Any]) -> ADUserInfo:
        """Convert a search result dict to ADUserInfo."""
        uac = data.get('userAccountControl', 512)
        if isinstance(uac, str):
            try:
                uac = int(uac)
            except ValueError:
                uac = 512

        enabled = not bool(uac & 0x2)

        # Check lockout
        lockout_time = data.get('lockoutTime', 0)
        if isinstance(lockout_time, str):
            try:
                lockout_time = int(lockout_time)
            except ValueError:
                lockout_time = 0
        locked = lockout_time > 0

        # Parse memberOf
        member_of = data.get('memberOf', [])
        if isinstance(member_of, str):
            member_of = [member_of]

        return ADUserInfo(
            dn=data.get('distinguishedName', ''),
            sam_account_name=data.get('sAMAccountName', ''),
            display_name=data.get('displayName', ''),
            given_name=data.get('givenName', ''),
            sn=data.get('sn', ''),
            email=data.get('mail', ''),
            office=data.get('physicalDeliveryOfficeName', ''),
            department=data.get('department', ''),
            title=data.get('title', ''),
            telephone=data.get('telephoneNumber', ''),
            mobile=data.get('mobile', ''),
            manager=data.get('manager', ''),
            member_of=member_of,
            enabled=enabled,
            locked_out=locked,
            password_expired=bool(uac & 0x800000),
            must_change_password=str(data.get('pwdLastSet', '0')) == '0',
            description=data.get('description', ''),
            path=data.get('distinguishedName', ''),
            sid=str(data.get('objectSid', '')),
            when_created=str(data.get('whenCreated', '')),
            when_changed=str(data.get('whenChanged', '')),
            logon_count=int(data.get('logonCount', 0) or 0),
            bad_password_count=int(data.get('badPwdCount', 0) or 0),
            home_drive=data.get('homeDrive', ''),
            home_directory=data.get('homeDirectory', ''),
            script_path=data.get('scriptPath', ''),
            profile_path=data.get('profilePath', ''),
            distinguished_name=data.get('distinguishedName', ''),
        )

    def _dict_to_computer(self, data: Dict[str, Any]) -> ADComputerInfo:
        """Convert a search result dict to ADComputerInfo."""
        uac = data.get('userAccountControl', 4096)
        if isinstance(uac, str):
            try:
                uac = int(uac)
            except ValueError:
                uac = 4096

        enabled = not bool(uac & 0x2)

        member_of = data.get('memberOf', [])
        if isinstance(member_of, str):
            member_of = [member_of]

        return ADComputerInfo(
            dn=data.get('distinguishedName', ''),
            name=data.get('name', data.get('cn', '')),
            sam_account_name=data.get('sAMAccountName', ''),
            operating_system=data.get('operatingSystem', ''),
            description=data.get('description', ''),
            enabled=enabled,
            when_created=str(data.get('whenCreated', '')),
            when_changed=str(data.get('whenChanged', '')),
            distinguished_name=data.get('distinguishedName', ''),
            dns_host_name=data.get('dnsHostName', ''),
            location=data.get('location', ''),
            managed_by=data.get('managedBy', ''),
            member_of=member_of,
            sid=str(data.get('objectSid', '')),
        )

    def _dict_to_group(self, data: Dict[str, Any]) -> ADGroupInfo:
        """Convert a search result dict to ADGroupInfo."""
        members = data.get('member', [])
        if isinstance(members, str):
            members = [members]

        group_type = data.get('groupType', -2147483646)
        if isinstance(group_type, str):
            try:
                group_type = int(group_type)
            except ValueError:
                group_type = -2147483646

        scope = "Global"
        if group_type & 0x4:
            scope = "DomainLocal"
        elif group_type & 0x8:
            scope = "Universal"

        type_str = "Security" if group_type & 0x80000000 else "Distribution"

        return ADGroupInfo(
            dn=data.get('distinguishedName', ''),
            name=data.get('name', ''),
            sam_account_name=data.get('sAMAccountName', ''),
            description=data.get('description', ''),
            group_scope=scope,
            group_type=type_str,
            members=members,
            member_count=len(members),
            when_created=str(data.get('whenCreated', '')),
            when_changed=str(data.get('whenChanged', '')),
            distinguished_name=data.get('distinguishedName', ''),
            managed_by=data.get('managedBy', ''),
            email=data.get('mail', ''),
        )

    def _dict_to_gpo(self, data: Dict[str, Any]) -> ADGPOInfo:
        """Convert a search result dict to ADGPOInfo."""
        return ADGPOInfo(
            dn=data.get('distinguishedName', ''),
            name=data.get('name', ''),
            display_name=data.get('displayName', ''),
            description=data.get('description', ''),
            when_created=str(data.get('whenCreated', '')),
            when_changed=str(data.get('whenChanged', '')),
            distinguished_name=data.get('distinguishedName', ''),
            flags=int(data.get('flags', 0) or 0),
            gpc_file_system_path=data.get('gPCFileSysPath', ''),
            version=int(data.get('versionNumber', 0) or 0),
        )

    def _get_dn_parent(self, dn: str) -> str:
        """Get the parent DN by removing the first component."""
        parts = dn.split(',')
        if len(parts) > 1:
            return ','.join(parts[1:])
        return self.config.base_dn if self.config else ""
