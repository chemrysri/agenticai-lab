import sqlite3

from config import ASSISTANT_DB_PATH


def register_sqlite_tools(mcp):
    @mcp.tool()
    def list_tables() -> dict:
        """
        List tables in the assistant SQLite database.
        """
        conn = sqlite3.connect(ASSISTANT_DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        )

        rows = cursor.fetchall()
        conn.close()

        return {
            "database": str(ASSISTANT_DB_PATH),
            "tables": [row[0] for row in rows],
        }

    @mcp.tool()
    def describe_table(table_name: str) -> dict:
        """
        Describe columns in one SQLite table.
        """
        conn = sqlite3.connect(ASSISTANT_DB_PATH)
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table_name})")

        columns = [
            {
                "cid": row[0],
                "name": row[1],
                "type": row[2],
                "not_null": bool(row[3]),
                "default": row[4],
                "primary_key": bool(row[5]),
            }
            for row in cursor.fetchall()
        ]

        conn.close()

        return {
            "table": table_name,
            "columns": columns,
        }

    @mcp.tool()
    def run_readonly_query(sql: str, max_rows: int = 50) -> dict:
        """
        Run a read-only SELECT query against the assistant SQLite database.
        """
        normalized = sql.strip().lower()

        if not normalized.startswith("select"):
            raise PermissionError("Only SELECT queries are allowed.")

        max_rows = max(1, min(int(max_rows), 200))

        conn = sqlite3.connect(ASSISTANT_DB_PATH)
        cursor = conn.cursor()

        cursor.execute(sql)
        rows = cursor.fetchmany(max_rows)
        columns = [description[0] for description in cursor.description]

        conn.close()

        return {
            "columns": columns,
            "rows": rows,
            "max_rows": max_rows,
        }