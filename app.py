import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Digital Legacy Manager",
    page_icon="🔐",
    layout="wide"
)

# =========================================================
# DATABASE
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# IMPORTANT:
# We are using a NEW database file.
# This avoids the old password_hash error.
DB_FILE = os.path.join(BASE_DIR, "streamlit_database.db")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    db = sqlite3.connect(DB_FILE)
    db.row_factory = sqlite3.Row
    return db


def create_database():

    db = get_db()

    # USERS
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # DIGITAL LEGACY
    db.execute("""
        CREATE TABLE IF NOT EXISTS legacy_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # EMERGENCY CONTACTS
    db.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            relationship TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # DOCUMENTS
    db.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # EMERGENCY INFORMATION
    db.execute("""
        CREATE TABLE IF NOT EXISTS emergency_information (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            blood_group TEXT,
            allergies TEXT,
            medical_conditions TEXT,
            emergency_notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    db.close()


create_database()

# =========================================================
# PASSWORD FUNCTIONS
# =========================================================

def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def check_password(password, password_hash):
    return hash_password(password) == password_hash


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"


# =========================================================
# REGISTER
# =========================================================

def register_page():

    st.title("🔐 Create Account")
    st.write("Create your Digital Legacy Manager account.")

    with st.form("register_form"):

        name = st.text_input("Full Name")

        email = st.text_input("Email Address")

        password = st.text_input(
            "Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Create Account",
            use_container_width=True
        )

        if submitted:

            if not name or not email or not password or not confirm_password:

                st.error("Please fill all fields.")

            elif password != confirm_password:

                st.error("Passwords do not match.")

            elif len(password) < 6:

                st.error("Password must contain at least 6 characters.")

            else:

                db = get_db()

                existing_user = db.execute(
                    "SELECT id FROM users WHERE email = ?",
                    (email.strip().lower(),)
                ).fetchone()

                if existing_user:

                    st.error("This email is already registered.")

                else:

                    db.execute(
                        """
                        INSERT INTO users
                        (name, email, password_hash)
                        VALUES (?, ?, ?)
                        """,
                        (
                            name.strip(),
                            email.strip().lower(),
                            hash_password(password)
                        )
                    )

                    db.commit()
                    db.close()

                    st.success(
                        "Account created successfully! Please login."
                    )

                    st.session_state.page = "Login"
                    st.rerun()

                db.close()


# =========================================================
# LOGIN
# =========================================================

def login_page():

    st.title("🔑 Login")

    st.write("Login to your Digital Legacy Manager.")

    with st.form("login_form"):

        email = st.text_input("Email Address")

        password = st.text_input(
            "Password",
            type="password"
        )

        submitted = st.form_submit_button(
            "Login",
            use_container_width=True
        )

        if submitted:

            db = get_db()

            user = db.execute(
                """
                SELECT *
                FROM users
                WHERE email = ?
                """,
                (email.strip().lower(),)
            ).fetchone()

            db.close()

            if user and check_password(
                password,
                user["password_hash"]
            ):

                st.session_state.logged_in = True
                st.session_state.user_id = user["id"]
                st.session_state.user_name = user["name"]

                st.session_state.page = "Dashboard"

                st.success("Login successful!")

                st.rerun()

            else:

                st.error(
                    "Invalid email or password."
                )


# =========================================================
# DASHBOARD
# =========================================================

def dashboard_page():

    st.title("🏠 Digital Legacy Manager")

    st.subheader(
        f"Welcome, {st.session_state.user_name} 👋"
    )

    db = get_db()

    user_id = st.session_state.user_id

    legacy_count = db.execute(
        "SELECT COUNT(*) FROM legacy_items WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]

    contact_count = db.execute(
        "SELECT COUNT(*) FROM contacts WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]

    document_count = db.execute(
        "SELECT COUNT(*) FROM documents WHERE user_id = ?",
        (user_id,)
    ).fetchone()[0]

    db.close()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Digital Legacy Items",
            legacy_count
        )

    with col2:
        st.metric(
            "Emergency Contacts",
            contact_count
        )

    with col3:
        st.metric(
            "Documents",
            document_count
        )

    st.divider()

    st.info(
        """
        Digital Legacy Manager helps you securely organize
        your important digital information, emergency contacts,
        legacy instructions and important documents.
        """
    )

    st.subheader("Quick Access")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(
            "📦 Digital Legacy",
            use_container_width=True
        ):
            st.session_state.page = "Digital Legacy"
            st.rerun()

    with col2:
        if st.button(
            "🚨 Emergency Contacts",
            use_container_width=True
        ):
            st.session_state.page = "Emergency Contacts"
            st.rerun()

    with col3:
        if st.button(
            "📄 Documents",
            use_container_width=True
        ):
            st.session_state.page = "Documents"
            st.rerun()


# =========================================================
# DIGITAL LEGACY
# =========================================================

def legacy_page():

    st.title("📦 Digital Legacy")

    user_id = st.session_state.user_id

    with st.form("legacy_form"):

        title = st.text_input(
            "Title",
            placeholder="Example: Important Online Accounts"
        )

        description = st.text_area(
            "Description",
            placeholder="Enter your legacy information..."
        )

        submitted = st.form_submit_button(
            "Add Legacy Information",
            use_container_width=True
        )

        if submitted:

            if not title:

                st.error("Please enter a title.")

            else:

                db = get_db()

                db.execute(
                    """
                    INSERT INTO legacy_items
                    (user_id, title, description)
                    VALUES (?, ?, ?)
                    """,
                    (
                        user_id,
                        title,
                        description
                    )
                )

                db.commit()
                db.close()

                st.success(
                    "Legacy information added successfully."
                )

                st.rerun()

    st.divider()

    db = get_db()

    items = db.execute(
        """
        SELECT *
        FROM legacy_items
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    db.close()

    if not items:

        st.info(
            "No digital legacy information added yet."
        )

    else:

        for item in items:

            with st.expander(
                f"📌 {item['title']}"
            ):

                st.write(
                    item["description"]
                )

                st.caption(
                    f"Created: {item['created_at']}"
                )


# =========================================================
# EMERGENCY CONTACTS
# =========================================================

def contacts_page():

    st.title("🚨 Emergency Contacts")

    user_id = st.session_state.user_id

    with st.form("contact_form"):

        name = st.text_input(
            "Contact Name"
        )

        email = st.text_input(
            "Email"
        )

        phone = st.text_input(
            "Phone Number"
        )

        relationship = st.text_input(
            "Relationship",
            placeholder="Example: Father / Mother / Friend"
        )

        submitted = st.form_submit_button(
            "Add Emergency Contact",
            use_container_width=True
        )

        if submitted:

            if not name:

                st.error(
                    "Please enter contact name."
                )

            else:

                db = get_db()

                db.execute(
                    """
                    INSERT INTO contacts
                    (user_id, name, email, phone, relationship)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        name,
                        email,
                        phone,
                        relationship
                    )
                )

                db.commit()
                db.close()

                st.success(
                    "Emergency contact added successfully."
                )

                st.rerun()

    st.divider()

    db = get_db()

    contacts = db.execute(
        """
        SELECT *
        FROM contacts
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    db.close()

    if not contacts:

        st.info(
            "No emergency contacts added yet."
        )

    else:

        for contact in contacts:

            with st.expander(
                f"👤 {contact['name']}"
            ):

                st.write(
                    f"**Email:** {contact['email'] or 'Not provided'}"
                )

                st.write(
                    f"**Phone:** {contact['phone'] or 'Not provided'}"
                )

                st.write(
                    f"**Relationship:** {contact['relationship'] or 'Not provided'}"
                )


# =========================================================
# DOCUMENTS
# =========================================================

def documents_page():

    st.title("📄 Documents")

    user_id = st.session_state.user_id

    uploaded_file = st.file_uploader(
        "Upload Important Document",
        type=[
            "pdf",
            "doc",
            "docx",
            "txt",
            "jpg",
            "jpeg",
            "png"
        ]
    )

    if uploaded_file is not None:

        if st.button(
            "Upload Document",
            use_container_width=True
        ):

            safe_filename = (
                f"{user_id}_"
                f"{datetime.now().strftime('%Y%m%d%H%M%S')}_"
                f"{uploaded_file.name}"
            )

            file_path = os.path.join(
                UPLOAD_FOLDER,
                safe_filename
            )

            with open(
                file_path,
                "wb"
            ) as file:

                file.write(
                    uploaded_file.getbuffer()
                )

            db = get_db()

            db.execute(
                """
                INSERT INTO documents
                (
                    user_id,
                    filename,
                    original_filename
                )
                VALUES (?, ?, ?)
                """,
                (
                    user_id,
                    safe_filename,
                    uploaded_file.name
                )
            )

            db.commit()
            db.close()

            st.success(
                "Document uploaded successfully."
            )

            st.rerun()

    st.divider()

    db = get_db()

    documents = db.execute(
        """
        SELECT *
        FROM documents
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    db.close()

    if not documents:

        st.info(
            "No documents uploaded yet."
        )

    else:

        for document in documents:

            file_path = os.path.join(
                UPLOAD_FOLDER,
                document["filename"]
            )

            st.write(
                f"📄 **{document['original_filename']}**"
            )

            if os.path.exists(file_path):

                with open(
                    file_path,
                    "rb"
                ) as file:

                    st.download_button(
                        label="⬇️ Download",
                        data=file.read(),
                        file_name=document[
                            "original_filename"
                        ],
                        key=f"download_{document['id']}"
                    )

            st.divider()


# =========================================================
# EMERGENCY INFORMATION
# =========================================================

def emergency_information_page():

    st.title("🩺 Emergency Information")

    user_id = st.session_state.user_id

    db = get_db()

    existing = db.execute(
        """
        SELECT *
        FROM emergency_information
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    db.close()

    current_blood = ""
    current_allergies = ""
    current_conditions = ""
    current_notes = ""

    if existing:

        current_blood = existing["blood_group"] or ""
        current_allergies = existing["allergies"] or ""
        current_conditions = existing["medical_conditions"] or ""
        current_notes = existing["emergency_notes"] or ""

    with st.form("emergency_form"):

        blood_group = st.text_input(
            "Blood Group",
            value=current_blood
        )

        allergies = st.text_area(
            "Allergies",
            value=current_allergies
        )

        medical_conditions = st.text_area(
            "Medical Conditions",
            value=current_conditions
        )

        emergency_notes = st.text_area(
            "Emergency Notes",
            value=current_notes
        )

        submitted = st.form_submit_button(
            "Save Emergency Information",
            use_container_width=True
        )

        if submitted:

            db = get_db()

            if existing:

                db.execute(
                    """
                    UPDATE emergency_information
                    SET
                    blood_group = ?,
                    allergies = ?,
                    medical_conditions = ?,
                    emergency_notes = ?
                    WHERE user_id = ?
                    """,
                    (
                        blood_group,
                        allergies,
                        medical_conditions,
                        emergency_notes,
                        user_id
                    )
                )

            else:

                db.execute(
                    """
                    INSERT INTO emergency_information
                    (
                        user_id,
                        blood_group,
                        allergies,
                        medical_conditions,
                        emergency_notes
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        blood_group,
                        allergies,
                        medical_conditions,
                        emergency_notes
                    )
                )

            db.commit()
            db.close()

            st.success(
                "Emergency information saved successfully."
            )

            st.rerun()


# =========================================================
# SETTINGS
# =========================================================

def settings_page():

    st.title("⚙️ Settings")

    st.write(
        f"**Name:** {st.session_state.user_name}"
    )

    db = get_db()

    user = db.execute(
        """
        SELECT email
        FROM users
        WHERE id = ?
        """,
        (st.session_state.user_id,)
    ).fetchone()

    db.close()

    if user:

        st.write(
            f"**Email:** {user['email']}"
        )

    st.divider()

    st.info(
        "Your Digital Legacy Manager account is active."
    )


# =========================================================
# LOGOUT
# =========================================================

def logout():

    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.page = "Login"

    st.rerun()


# =========================================================
# MAIN APPLICATION
# =========================================================

if not st.session_state.logged_in:

    st.sidebar.title("🔐 Digital Legacy Manager")

    menu = st.sidebar.radio(
        "Menu",
        [
            "Login",
            "Create Account"
        ]
    )

    if menu == "Login":

        login_page()

    else:

        register_page()

else:

    st.sidebar.title(
        "🔐 Digital Legacy Manager"
    )

    st.sidebar.write(
        f"Welcome, {st.session_state.user_name}"
    )

    st.sidebar.divider()

    menu = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Digital Legacy",
            "Emergency Contacts",
            "Documents",
            "Emergency Information",
            "Settings"
        ]
    )

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        logout()

    if menu == "Dashboard":

        dashboard_page()

    elif menu == "Digital Legacy":

        legacy_page()

    elif menu == "Emergency Contacts":

        contacts_page()

    elif menu == "Documents":

        documents_page()

    elif menu == "Emergency Information":

        emergency_information_page()

    elif menu == "Settings":

        settings_page()
