# client_page.py
import streamlit as st
from db_utils import get_db_connection
from datetime import datetime, timedelta


# Generate new query_id, we are taking default from 15
def generate_new_query_id(start_id=15):
    """
    Generates a new query ID starting from start_id.
    Skips any existing IDs to avoid duplicates.
    """
    conn = get_db_connection()
    if not conn:
        return f"Q{start_id:04d}"

    try:
        cursor = conn.cursor()
        # Fetch all numeric parts of query_id
        cursor.execute(
            "SELECT CAST(SUBSTRING(query_id, 2) AS UNSIGNED) FROM synthetic_client_queries"
        )
        existing_ids = [row[0] for row in cursor.fetchall() if row[0] is not None]

        # Start from start_id and find the first unused number
        new_id = start_id
        while new_id in existing_ids:
            new_id += 1

        return f"Q{new_id:04d}"

    except Exception as e:
        print(f"Error generating new query ID: {e}")
        return f"Q{start_id:04d}"
    finally:
        if "cursor" in locals() and cursor:
            cursor.close()
        if "conn" in locals() and conn:
            conn.close()


# Show client page in UI
def show_client_page():
    st.subheader("Client Dashboard")

    # Predefined query headings used in client page
    query_options = [
        "Account Suspension",
        "Billing Problem",
        "Bug Report",
        "Data Export",
        "Feature Request",
        "Login Issue",
        "Payment Failure",
        "Subscription Cancellation",
        "Technical Support",
        "UI Feedback",
    ]

    # Reset fields safely before widgets (flag method)
    if "reset_fields" in st.session_state and st.session_state.reset_fields:
        st.session_state.query_description = ""
        st.session_state.query_heading = query_options[0]
        st.session_state.client_mobile = ""
        st.session_state.reset_fields = False

    # Initialize session state
    if "client_email_input" not in st.session_state:
        st.session_state.client_email_input = st.session_state.get("client_email", "")
    if "client_mobile" not in st.session_state:
        st.session_state.client_mobile = ""
    if "query_heading" not in st.session_state:
        st.session_state.query_heading = query_options[0]
    if "query_description" not in st.session_state:
        st.session_state.query_description = ""

    # Input widgets
    client_email = st.text_input(
        "Email",
        key="client_email_input",  # no value= to avoid warning
        disabled=True,
    )
    client_mobile = st.text_input("Mobile Number", key="client_mobile")
    query_heading = st.selectbox(
        "Query Heading",
        options=query_options,
        index=(
            query_options.index(st.session_state.query_heading)
            if st.session_state.query_heading in query_options
            else 0
        ),
        key="query_heading",
    )
    query_description = st.text_area(
        "Query Description",
        key="query_description",
    )

    # Buttons
    col1, col2 = st.columns(2)
    with col1:
        submit_clicked = st.button("Submit Query")
    with col2:
        logout_clicked = st.button("Logout", key="client_logout_btn")

    # Logout action
    if logout_clicked:
        st.session_state.clear()
        st.rerun()

    # Submit Query action
    if submit_clicked:
        if not client_email or not client_mobile or not query_description:
            st.error("Please fill in all required fields.")
        else:
            new_query_id = generate_new_query_id()
            if not new_query_id:
                st.error("Failed to generate a new Query ID.")
            else:
                date_raised = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                conn = None
                cursor = None
                try:
                    conn = get_db_connection()
                    if conn:
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            INSERT INTO synthetic_client_queries
                            (query_id, client_email, client_mobile, query_heading, query_description, query_status, date_raised, date_closed)
                            VALUES (%s, %s, %s, %s, %s, 'Open', %s, NULL)
                        """,
                            (
                                new_query_id,
                                client_email,
                                client_mobile,
                                query_heading,
                                query_description,
                                date_raised,
                            ),
                        )
                        conn.commit()

                        # store success message for 5 seconds
                        st.session_state.success_message = f"Query {new_query_id} submitted successfully at {date_raised}!"
                        st.session_state.success_until = datetime.now() + timedelta(
                            seconds=5
                        )

                        # reset fields on next run
                        st.session_state.reset_fields = True
                        st.rerun()

                except Exception as e:
                    st.error(f"Failed to submit query: {e}")
                finally:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()

    # Show success message if still valid
    if "success_message" in st.session_state:
        if datetime.now() < st.session_state.success_until:
            st.success(st.session_state.success_message)
        else:
            # clear message after 5 sec
            st.session_state.pop("success_message", None)
            st.session_state.pop("success_until", None)
