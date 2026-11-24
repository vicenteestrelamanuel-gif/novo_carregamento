import streamlit as st
import libsql
from types import SimpleNamespace

def get_client():
    url = st.secrets["TURSO_DATABASE_URL"]
    token = st.secrets["TURSO_AUTH_TOKEN"]

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
