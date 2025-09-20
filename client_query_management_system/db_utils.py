# db_utils.py
import mysql.connector
import streamlit as st
from datetime import datetime


def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="aira",
            database="cqms",
        )
        return conn
    except mysql.connector.Error as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None


def update_query_status_and_close(query_id, new_heading, new_description):
    """
    Updates query heading/description, closes it, and sets date_closed.
    """
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                UPDATE synthetic_client_queries
                SET query_heading = %s,
                    query_description = %s,
                    query_status = 'Closed',
                    date_closed = %s
                WHERE query_id = %s
            """
            cursor.execute(
                query,
                (
                    new_heading,
                    new_description,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    query_id,
                ),
            )
            conn.commit()
            return True
        except Exception as e:
            import streamlit as st

            st.error(f"Failed to update and close query: {e}")
            return False
        finally:
            cursor.close()
            conn.close()
    return False
