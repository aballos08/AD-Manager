"""
Tamper-evident audit trail for the AD Manager.

Every mutation performed through ADConnection is appended as a JSON line
(JSONL) to a single audit file:

    Windows :  %LOCALAPPDATA%\\AD-Manager\\audit_trail.jsonl
    Other   :  ~/.local/share/AD-Manager/audit_trail.jsonl

Design notes
------------
* Append-only JSONL: entries are never modified or deleted in place, and
  each line carries a chained SHA-256 hash of the previous line, so any
  later edit or removal of an entry breaks the hash chain.
* The log never raises: if the filesystem is unavailable, logging
  failures are swallowed (best-effort, like syslog).
* Operator identity comes from the AD login dialog, falling back to the
  local OS user. No passwords are ever recorded.
"""

import csv
import hashlib
import json
import logging
import os
import socket
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Actions that change AD objects.
ACTION_CREATE = "create"
ACTION_DELETE = "delete"
ACTION_MODIFY = "modify"
VALID_ACTIONS = {ACTION_CREATE, ACTION_DELETE, ACTION_MODIFY}

GENESIS_HASH = "0" * 64


class AuditEntry:
    """One recorded AD change."""

    __slots__ = (
        "timestamp", "operator", "host", "action", "object_type",
        "object_name", "details", "result", "prev_hash", "hash",
    )

    def __init__(
        self,
        action: str,
        object_type: str,
        object_name: str,
        details: str = "",
        result: str = "success",
        operator: Optional[str] = None,
        timestamp: Optional[str] = None,
        host: Optional[str] = None,
        prev_hash: Optional[str] = None,
    ):
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()
        self.operator = operator or get_operator()
        self.host = host or socket.gethostname()
        self.action = action
        if action not in VALID_ACTIONS:
            raise ValueError(f"Unknown audit action: {action!r}")
        self.object_type = object_type
        self.object_name = object_name
        self.details = details
        self.result = result  # success | failure
        self.prev_hash = prev_hash
        self.hash = None

    # ── serialization ─────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "timestamp": self.timestamp,
            "operator": self.operator,
            "host": self.host,
            "action": self.action,
            "object_type": self.object_type,
            "object_name": self.object_name,
            "details": self.details,
            "result": self.result,
        }
        if self.prev_hash is not None:
            d["prev_hash"] = self.prev_hash
            d["hash"] = self.hash
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AuditEntry":
        entry = cls(
            action=d.get("action", ACTION_MODIFY),
            object_type=d.get("object_type", "unknown"),
            object_name=d.get("object_name", ""),
            details=d.get("details", ""),
            result=d.get("result", "success"),
            operator=d.get("operator"),
            timestamp=d.get("timestamp"),
            host=d.get("host"),
            prev_hash=d.get("prev_hash"),
        )
        entry.hash = d.get("hash")  # restore stored chain hash
        return entry

    def _core_payload(self) -> str:
        d = self.to_dict()
        d.pop("prev_hash", None)
        d.pop("hash", None)
        return json.dumps(d, sort_keys=True, ensure_ascii=False)

    def compute_hash(self, prev_hash: str) -> str:
        self.prev_hash = prev_hash
        return hashlib.sha256(
            (prev_hash + self._core_payload()).encode("utf-8")
        ).hexdigest()

    def to_json_line(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


def get_operator() -> str:
    """Operator identity: AD account when set, else local OS user."""
    ad_user = current_ad_user
    if ad_user:
        return ad_user
    user = os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"
    return f"{user}@{socket.gethostname()}"


# Process-wide identity of the currently logged-in AD operator.
# Set by ADConnection.connect() on successful login; never logged out
# explicitly — the value is simply overwritten on the next connect.
current_ad_user: Optional[str] = None


class AuditLog:
    """Append-only, hash-chained audit store (JSONL on disk)."""

    def __init__(self, file_path: Optional[str] = None):
        if file_path is None:
            if os.name == "nt":
                base = os.environ.get(
                    "LOCALAPPDATA", os.path.expanduser("~")
                )
                base = os.path.join(base, "AD-Manager")
            else:
                base = os.path.join(
                    os.path.expanduser("~"), ".local", "share", "AD-Manager"
                )
            os.makedirs(base, exist_ok=True)
            file_path = os.path.join(base, "audit_trail.jsonl")
        self.file_path = file_path
        self._last_hash: Optional[str] = None
        self._loaded_upto = 0  # entries returned by last load

    # ── chain state ───────────────────────────────────────────────

    def _ensure_chain_state(self) -> None:
        """Compute last hash lazily by scanning the file tail."""
        if self._last_hash is not None:
            return
        entries = self._read_all_entries()
        if entries:
            self._loaded_upto = len(entries)
            last = entries[-1]
            self._last_hash = last.hash or GENESIS_HASH
        else:
            self._loaded_upto = 0
            self._last_hash = GENESIS_HASH

    def _read_all_entries(self) -> List[AuditEntry]:
        entries: List[AuditEntry] = []
        if not os.path.exists(self.file_path):
            return entries
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entries.append(AuditEntry.from_dict(json.loads(line)))
                    except (json.JSONDecodeError, ValueError):
                        # Skip corrupt lines but keep going.
                        continue
        except OSError as e:
            logger.error(f"Could not read audit log: {e}")
        return entries

    # ── writing ───────────────────────────────────────────────────

    def log(
        self,
        action: str,
        object_type: str,
        object_name: str,
        details: str = "",
        result: str = "success",
    ) -> Optional[AuditEntry]:
        """Append one audit entry. Never raises."""
        try:
            self._ensure_chain_state()
            entry = AuditEntry(
                action=action,
                object_type=object_type,
                object_name=object_name,
                details=details,
                result=result,
                operator=get_operator(),
                prev_hash=self._last_hash or GENESIS_HASH,
            )
            entry.hash = entry.compute_hash(entry.prev_hash)
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(entry.to_json_line() + "\n")
            self._last_hash = entry.hash
            self._loaded_upto += 1
            return entry
        except Exception as e:  # auditing must never break the app
            logger.error(f"Audit log write failed: {e}")
            return None

    # ── reading / filtering ───────────────────────────────────────

    def load(self, limit: int = 5000) -> List[AuditEntry]:
        """Load the most recent `limit` entries (oldest first)."""
        entries = self._read_all_entries()
        self._loaded_upto = len(entries)
        if entries and entries[-1].hash:
            self._last_hash = entries[-1].hash
        return entries[-limit:] if limit else entries

    def verify(self) -> Dict[str, Any]:
        """Recompute the hash chain. Returns verification report."""
        entries = self._read_all_entries()
        prev = GENESIS_HASH
        broken_at: Optional[int] = None
        for i, e in enumerate(entries):
            expected = hashlib.sha256(
                (prev + e._core_payload()).encode("utf-8")
            ).hexdigest()
            if not e.hash or e.hash != expected:
                broken_at = i
                break
            prev = e.hash
        return {
            "total": len(entries),
            "ok": broken_at is None,
            "broken_at": broken_at,
            "last_hash": prev if broken_at is None else None,
        }

    def export_csv(self, out_path: str, entries: List[AuditEntry]) -> int:
        """Export entries to CSV. Returns rows written (excl. header)."""
        with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "Timestamp (UTC)", "Operator", "Host", "Action",
                    "Object Type", "Object", "Details", "Result",
                    "Entry Hash",
                ]
            )
            for e in entries:
                w.writerow(
                    [
                        e.timestamp, e.operator, e.host, e.action,
                        e.object_type, e.object_name, e.details,
                        e.result, e.hash or "",
                    ]
                )
        return len(entries)
