# app.py
import streamlit as st
import hashlib
from db_utils import get_db_connection


# Hash password function :
def hash_password(password):
    """Hashes a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


# Authenticate user function
def authenticate_user(username, password, status):
    """Authenticates a user against the database."""
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    hashed_password = hash_password(password)
    query = "SELECT * FROM users WHERE username=%s AND hashed_password=%s AND status=%s"
    cursor.execute(query, (username, hashed_password, status))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


# Register user function
def register_user(username, password, email, status):
    """Registers a new user in the database."""
    conn = get_db_connection()
    if not conn:
        return False
    cursor = conn.cursor()
    try:
        # Query to check if username/email exists
        cursor.execute(
            "SELECT * FROM users WHERE username=%s OR client_email=%s",
            (username, email),
        )
        if cursor.fetchone():
            st.error("Username or email already exists.")
            return False

        # Inserting the username, hashed passowrd, email and status in users table
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, hashed_password, client_email, status) VALUES (%s, %s, %s, %s)",
            (username, hashed_password, email, status),
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Registration failed: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


# Main App function
def main():
    """Main function to run the Streamlit app."""
    st.title("Client Query Management System")

    # Initialize session state
    for key in ["logged_in", "username", "status", "client_email"]:
        if key not in st.session_state:
            st.session_state[key] = None
    if st.session_state.logged_in is None:
        st.session_state.logged_in = False

    # Check if a user is logged in
    if st.session_state.logged_in:
        st.write(f"Welcome, **{st.session_state.username}**!")

        # Route based on user status
        if st.session_state.status == "Client":
            from client_page import show_client_page

            # Show client page
            show_client_page()
        elif st.session_state.status == "Admin":
            from admin_page import show_admin_page

            # Show Admin page
            show_admin_page()
    else:
        # Show login/register options
        action = st.radio("Choose an option:", ["Login", "Register"])

        # Login section
        if action == "Login":
            st.subheader("Login")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            status = st.selectbox("Login as:", ["Client", "Admin"])

            if st.button("Login"):
                user = authenticate_user(username, password, status)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user["username"]
                    st.session_state.status = user["status"]
                    st.session_state.client_email = user.get("client_email", None)
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")

        # Register section
        elif action == "Register":
            st.subheader("Register")
            username = st.text_input("Username", key="reg_username")
            email = st.text_input("Email", key="reg_email")
            password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input(
                "Confirm Password", type="password", key="confirm_password"
            )
            status = st.selectbox("Register as:", ["Client", "Admin"])

            if st.button("Register"):
                if password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    if register_user(username, password, email, status):
                        st.success("Registration successful! You can now login.")
                    else:
                        st.error("Registration failed.")


if __name__ == "__main__":
    main()
