import sqlite3
from pathlib import Path
import pandas as pd


class AuditStore:

    def __init__(self, db_path):
        self.db_path = Path(db_path)

        # Create parent folder if it does not exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._initialize_database()

    def _connect(self):
        connection = sqlite3.connect(
            self.db_path,
            timeout=10
        )

        # Helps with safe concurrent access
        connection.execute("PRAGMA journal_mode=WAL")

        # Enforce database relationships
        connection.execute("PRAGMA foreign_keys=ON")

        return connection

    def _initialize_database(self):
        with self._connect() as connection:

            connection.execute("""
                CREATE TABLE IF NOT EXISTS decision_audit (
                    decision_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    locality TEXT NOT NULL,
                    recommended_priority TEXT NOT NULL,
                    recommended_action TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    override_reason TEXT,
                    priority_score REAL NOT NULL,
                    sli REAL NOT NULL,
                    slo REAL NOT NULL,
                    user_impact REAL NOT NULL,
                    rainfall_mm REAL NOT NULL
                )
            """)

            connection.commit()

    def save_decision(self, record):

        with self._connect() as connection:

            connection.execute("""
                INSERT INTO decision_audit (
                    decision_id,
                    timestamp,
                    locality,
                    recommended_priority,
                    recommended_action,
                    decision,
                    override_reason,
                    priority_score,
                    sli,
                    slo,
                    user_impact,
                    rainfall_mm
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record["decision_id"],
                record["timestamp"],
                record["locality"],
                record["recommended_priority"],
                record["recommended_action"],
                record["decision"],
                record["override_reason"],
                record["priority_score"],
                record["sli"],
                record["slo"],
                record["user_impact"],
                record["rainfall_mm"]
            ))

            connection.commit()

    def get_all_decisions(self):

        with self._connect() as connection:

            return pd.read_sql_query(
                """
                SELECT *
                FROM decision_audit
                ORDER BY timestamp DESC
                """,
                connection
            )