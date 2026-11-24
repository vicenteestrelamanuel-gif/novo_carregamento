
import streamlit as st
import libsql
import pandas as pd
from types import SimpleNamespace


def get_client():
    try:
        url = st.secrets["TURSO_DATABASE_URL"]
        token = st.secrets["TURSO_AUTH_TOKEN"]
    except Exception as exc:
        raise RuntimeError(
            "Configura TURSO_DATABASE_URL e TURSO_AUTH_TOKEN "
            "nos Secrets do Streamlit Cloud."
        ) from exc

    return libsql.connect(
        database=url,
        auth_token=token
    )


def execute(sql, args=()):
    client = get_client()
    try:
        cursor = client.execute(sql, args)
        client.commit()

        columns = (
            [column[0] for column in cursor.description]
            if cursor.description else []
        )

        result_rows = cursor.fetchall() if columns else []

        return SimpleNamespace(
            rows=result_rows,
            columns=columns
        )
    finally:
        client.close()


def query_df(sql, args=()):
    result = execute(sql, args)
    return pd.DataFrame(
        result.rows,
        columns=result.columns
    )


def rows(sql, args=()):
    result = execute(sql, args)
    return [
        dict(zip(result.columns, row))
        for row in result.rows
    ]


def init_db():
    statements = [
        """CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT,
            model TEXT,
            year INTEGER,
            plate TEXT,
            fuel_type TEXT NOT NULL DEFAULT 'Elétrico',
            battery_kwh REAL,
            wltp_km REAL,
            fuel_capacity_l REAL,
            purchase_date TEXT,
            purchase_km INTEGER,
            status TEXT NOT NULL DEFAULT 'Atual',
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS charging (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            event_date TEXT NOT NULL,
            soc_start REAL,
            soc_end REAL,
            kwh REAL NOT NULL,
            price_kwh REAL NOT NULL,
            total_cost REAL NOT NULL,
            odometer INTEGER,
            location TEXT,
            provider TEXT,
            notes TEXT,
            fingerprint TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS fuelings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            event_date TEXT NOT NULL,
            odometer INTEGER,
            litres REAL NOT NULL,
            price_litre REAL NOT NULL,
            total_cost REAL NOT NULL,
            full_tank INTEGER DEFAULT 0,
            station TEXT,
            notes TEXT,
            fingerprint TEXT UNIQUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER,
            event_date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL,
            odometer INTEGER,
            recurring INTEGER DEFAULT 0,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS maintenance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            event_date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            amount REAL DEFAULT 0,
            odometer INTEGER,
            next_date TEXT,
            next_odometer INTEGER,
            workshop TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT,
            origin TEXT,
            destination TEXT,
            distance_km REAL,
            total_cost REAL,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER,
            title TEXT NOT NULL,
            category TEXT,
            expiry_date TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""",

        """CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )"""
    ]

    for statement in statements:
        execute(statement)

    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_charging_vehicle_date ON charging(vehicle_id,event_date)",
        "CREATE INDEX IF NOT EXISTS idx_fuelings_vehicle_date ON fuelings(vehicle_id,event_date)",
        "CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(event_date)",
        "CREATE INDEX IF NOT EXISTS idx_maintenance_date ON maintenance(event_date)"
    ]

    for statement in indexes:
        execute(statement)
