import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

from .models import AuditLogEntry, Recommendation


DATABASE_PATH = Path(
    os.getenv(
        "COSTOPTI_DB_PATH",
        str(Path(__file__).resolve().parent.parent / "costopti.db"),
    )
)
APPROVAL_WAIT_MINUTES = int(os.getenv("COSTOPTI_APPROVAL_WAIT_MINUTES", "3"))
DEMO_RECOMMENDATION_COUNT = int(os.getenv("COSTOPTI_DEMO_RECOMMENDATION_COUNT", "3"))


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                id TEXT PRIMARY KEY,
                resource_id TEXT NOT NULL,
                resource_name TEXT NOT NULL,
                action TEXT NOT NULL,
                estimated_monthly_savings_inr REAL NOT NULL,
                waiting_period_hours INTEGER NOT NULL,
                status TEXT NOT NULL,
                decision_note TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recommendation_id TEXT NOT NULL,
                resource_id TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT NOT NULL
            );
            """
        )
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(recommendations)")
        }
        if "approval_deadline" not in columns:
            connection.execute(
                "ALTER TABLE recommendations ADD COLUMN approval_deadline TEXT"
            )
        pending_rows = connection.execute(
            "SELECT id, waiting_period_hours, approval_deadline FROM recommendations "
            "WHERE status = 'pending_approval'"
        ).fetchall()
        for row in pending_rows:
            if (
                row["waiting_period_hours"] != APPROVAL_WAIT_MINUTES
                or row["approval_deadline"] is None
            ):
                connection.execute(
                    "UPDATE recommendations SET waiting_period_hours = ?, approval_deadline = ? WHERE id = ?",
                    (
                        APPROVAL_WAIT_MINUTES,
                        _deadline_after_minutes(APPROVAL_WAIT_MINUTES),
                        row["id"],
                    ),
                )


def _deadline_after_minutes(minutes: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def save_recommendation(recommendation: Recommendation) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT OR IGNORE INTO recommendations
            (id, resource_id, resource_name, action, estimated_monthly_savings_inr,
             waiting_period_hours, status, decision_note, approval_deadline)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recommendation.id,
                recommendation.resource_id,
                recommendation.resource_name,
                recommendation.action,
                recommendation.estimated_monthly_savings_inr,
                recommendation.waiting_period_hours,
                recommendation.status,
                recommendation.decision_note,
                recommendation.approval_deadline,
            ),
        )


def list_saved_recommendations() -> List[Recommendation]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM recommendations ORDER BY id"
        ).fetchall()
    return [Recommendation.model_validate(dict(row)) for row in rows]


def update_recommendation(recommendation: Recommendation) -> None:
    with get_connection() as connection:
        connection.execute(
            "UPDATE recommendations SET status = ?, decision_note = ?, approval_deadline = ? WHERE id = ?",
            (
                recommendation.status,
                recommendation.decision_note,
                recommendation.approval_deadline,
                recommendation.id,
            ),
        )


def save_audit_log(entry: AuditLogEntry) -> None:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO audit_logs
            (recommendation_id, resource_id, action, status, message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                entry.recommendation_id,
                entry.resource_id,
                entry.action,
                entry.status,
                entry.message,
            ),
        )


def list_saved_audit_logs() -> List[AuditLogEntry]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT recommendation_id, resource_id, action, status, message
            FROM audit_logs ORDER BY id
            """
        ).fetchall()
    return [AuditLogEntry.model_validate(dict(row)) for row in rows]