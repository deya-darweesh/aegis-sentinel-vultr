"""Audit Ledger Adapter (Dual-Sink: JSONL + SQLite).

Implements AuditLedgerPort.
Maintains append-only audit_log.jsonl for tailing and SQLite for fast queries,
enforcing SHA-256 hash chaining on all lifecycle transitions.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

from application.dtos.audit_event_dto import AuditEventDTO
from application.dtos.execution_receipt_dto import ExecutionReceiptDTO
from application.ports.i_audit_ledger import IAuditLedger
from domain.values.execution_receipt import ExecutionReceipt, SecurityStatus
from infrastructure.config import settings
from infrastructure.crypto.hash_chainer import HashChainer


class AuditLedgerAdapter(IAuditLedger):
    """Dual-sink append-only audit log."""

    def __init__(self, log_dir: Optional[Path] = None):
        self.log_dir = log_dir or settings.LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = self.log_dir / "audit_log.jsonl"
        self.db_path = self.log_dir / "audit.db"
        self._last_chain_hash = HashChainer.GENESIS_HASH
        self._init_sqlite()

    def _init_sqlite(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    task_slug TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    container_id TEXT,
                    payload TEXT NOT NULL,
                    prev_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS receipts (
                    receipt_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    task_slug TEXT NOT NULL,
                    status TEXT NOT NULL,
                    exit_code INTEGER NOT NULL,
                    duration_ms REAL NOT NULL,
                    digest_sha256 TEXT NOT NULL,
                    ed25519_signature TEXT,
                    payload_json TEXT NOT NULL
                )
            """)
            conn.commit()

            # Recover latest chain hash if DB already has records
            cursor = conn.cursor()
            cursor.execute("SELECT event_hash FROM audit_events ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                self._last_chain_hash = row[0]

    def append_event(
        self,
        event_id: str,
        task_slug: str,
        event_type: str,
        payload: dict,
        container_id: Optional[str] = None,
    ) -> str:
        timestamp = time.time()
        new_hash = HashChainer.compute_next_hash(
            prev_hash=self._last_chain_hash,
            timestamp=timestamp,
            event_type=event_type,
            payload=payload,
        )

        record = {
            "event_id": event_id,
            "timestamp": timestamp,
            "task_slug": task_slug,
            "event_type": event_type,
            "container_id": container_id,
            "payload": payload,
            "prev_hash": self._last_chain_hash,
            "event_hash": new_hash,
        }

        # 1. Append to JSONL
        with self.jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        # 2. Insert into SQLite
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO audit_events
                (event_id, timestamp, task_slug, event_type, container_id, payload, prev_hash, event_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    timestamp,
                    task_slug,
                    event_type,
                    container_id,
                    json.dumps(payload),
                    self._last_chain_hash,
                    new_hash,
                ),
            )
            conn.commit()

        self._last_chain_hash = new_hash
        return new_hash

    def get_latest_chain_hash(self) -> str:
        return self._last_chain_hash

    def persist_receipt(self, receipt: ExecutionReceipt) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO receipts
                (receipt_id, timestamp, task_slug, status, exit_code, duration_ms, digest_sha256, ed25519_signature, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt.receipt_id,
                    receipt.timestamp,
                    receipt.task_slug,
                    receipt.status.value,
                    receipt.exit_code,
                    receipt.duration_ms,
                    receipt.compute_canonical_digest(),
                    receipt.ed25519_signature,
                    json.dumps(receipt.to_dict()),
                ),
            )
            conn.commit()

    def get_receipt(self, receipt_id: str) -> Optional[ExecutionReceiptDTO]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT receipt_id, timestamp, task_slug, status, exit_code, duration_ms,
                       digest_sha256, ed25519_signature, payload_json
                FROM receipts WHERE receipt_id = ?
                """,
                (receipt_id,),
            )
            row = cursor.fetchone()
            if row:
                payload = json.loads(row[8])
                return ExecutionReceiptDTO(
                    receipt_id=row[0],
                    timestamp=row[1],
                    task_slug=row[2],
                    status=row[3],
                    exit_code=row[4],
                    duration_ms=row[5],
                    memory_peak_mb=float(payload.get("memory_peak_mb", 0.0)),
                    runtime_engine=str(payload.get("runtime_engine", "runsc")),
                    container_id=str(payload.get("container_id", "none")),
                    digest_sha256=row[6],
                    ed25519_signature=row[7],
                    public_key=str(payload.get("public_key", "")) or None,
                    violation=payload.get("violation"),
                )
        return None

    def list_recent_events(self, limit: int = 50) -> List[AuditEventDTO]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT event_id, timestamp, task_slug, event_type, container_id, payload, prev_hash, event_hash FROM audit_events ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cursor.fetchall()
            return [
                AuditEventDTO(
                    event_id=r[0],
                    timestamp=r[1],
                    task_slug=r[2],
                    event_type=r[3],
                    container_id=r[4],
                    payload=json.loads(r[5]),
                    prev_hash=r[6],
                    event_hash=r[7],
                )
                for r in rows
            ]
