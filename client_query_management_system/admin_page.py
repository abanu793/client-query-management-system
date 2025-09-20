import streamlit as st
import pandas as pd
from db_utils import get_db_connection, update_query_status_and_close
from datetime import datetime


def show_admin_page():
    st.subheader("Admin Dashboard")

    conn = get_db_connection()
    if not conn:
        st.error("Database connection failed.")
        return

    try:

        # Filters functionality
        st.markdown("### Filters")
        status_filter = st.selectbox(
            "Filter by Status", ["All", "Open", "Closed"], index=0
        )

        headings_query = "SELECT DISTINCT query_heading FROM synthetic_client_queries"
        headings_df = pd.read_sql(headings_query, conn)
        heading_options = ["All"] + headings_df["query_heading"].dropna().astype(
            str
        ).tolist()
        heading_filter = st.selectbox("Filter by Heading", heading_options, index=0)

        # Fetch filtered queries
        query = """
            SELECT query_id, query_heading, query_description, query_status, date_raised, date_closed
            FROM synthetic_client_queries
        """
        conditions = []
        params = []

        if status_filter != "All":
            conditions.append("query_status = %s")
            params.append(status_filter)

        if heading_filter != "All":
            conditions.append("query_heading = %s")
            params.append(heading_filter)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY date_raised DESC"

        df = pd.read_sql(query, conn, params=params)

        # Highlight closed queries to avoid confusion
        def highlight_closed(row):
            if str(row["query_status"]).strip() == "Closed":
                return ["background-color: #d4edda"] * len(row)
            return [""] * len(row)

        st.markdown("### Client Queries")
        if df.empty:
            st.info("No queries found matching filters.")
        else:
            st.dataframe(
                df.style.apply(highlight_closed, axis=1), use_container_width=True
            )

        # Close/Edit Open Queries
        st.markdown("---")
        st.subheader("Edit & Close Open Queries")

        open_queries = df[df["query_status"].str.strip() == "Open"]

        # Apply heading filter
        if heading_filter != "All":
            open_queries = open_queries[open_queries["query_heading"] == heading_filter]

        if open_queries.empty:
            st.info("No open queries available for editing.")
        else:
            open_ids = open_queries["query_id"].astype(str).tolist()

            if (
                "selected_query_id_admin" not in st.session_state
                or st.session_state.selected_query_id_admin not in open_ids
            ):
                st.session_state.selected_query_id_admin = open_ids[0]

            query_id_to_edit = st.selectbox(
                "Select Open Query ID",
                options=open_ids,
                index=open_ids.index(st.session_state.selected_query_id_admin),
                key="close_query_selector_admin",
            )
            st.session_state.selected_query_id_admin = query_id_to_edit

            selected_row_df = open_queries[open_queries["query_id"] == query_id_to_edit]
            if not selected_row_df.empty:
                selected_row = selected_row_df.iloc[0]

                new_heading = st.text_input(
                    "Query Heading",
                    value=selected_row.get("query_heading", ""),
                    key="close_heading_input_admin",
                )
                new_description = st.text_area(
                    "Query Description",
                    value=selected_row.get("query_description", ""),
                    height=200,
                    key="close_description_input_admin",
                )

                if st.button("Save & Close Query", key="save_close_button_admin"):
                    success = update_query_status_and_close(
                        query_id_to_edit, new_heading, new_description
                    )
                    if success:
                        st.success(f"Query {query_id_to_edit} closed successfully.")
                        st.session_state.selected_query_id_admin = None
                        st.rerun()
                    else:
                        st.error("Failed to close query.")

    except Exception as e:
        st.error(f"Error fetching queries: {e}")
    finally:
        conn.close()

    # Logout
    col1, col2 = st.columns([3, 1])  # 3:1 ratio
    with col2:
        if st.button("Logout", key="admin_logout_unique"):
            st.session_state.logged_in = False
            st.rerun()
