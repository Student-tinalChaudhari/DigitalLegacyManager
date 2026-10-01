import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime, date

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Digital Legacy Manager",
    page_icon="🔐",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "streamlit_database.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================================================
# DATABASE
# =========================================================
def get_db():
    db = sqlite3.connect(DB_FILE)
    db.row_factory = sqlite3.Row
    return db


def add_column_if_missing(db, table, column, definition):
    columns = [row["name"] for row in db.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in columns:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def create_database():
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS legacy_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

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

    db.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

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

    db.execute("""
        CREATE TABLE IF NOT EXISTS government_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            document_type TEXT NOT NULL,
            required_document TEXT NOT NULL,
            original_filename TEXT,
            stored_filename TEXT,
            status TEXT DEFAULT 'Not Uploaded',
            verification_status TEXT DEFAULT 'Pending',
            verification_reason TEXT,
            uploaded_at TEXT,
            has_expiry INTEGER DEFAULT 0,
            issue_date TEXT,
            expiry_date TEXT
        )
    """)

    # Safe migration for older versions of this app.
    add_column_if_missing(db, "government_documents", "verification_reason", "TEXT")
    add_column_if_missing(db, "government_documents", "has_expiry", "INTEGER DEFAULT 0")
    add_column_if_missing(db, "government_documents", "issue_date", "TEXT")
    add_column_if_missing(db, "government_documents", "expiry_date", "TEXT")

    db.commit()
    db.close()


create_database()

# =========================================================
# GOVERNMENT DOCUMENT CHECKLIST
# =========================================================
GOVERNMENT_DOCUMENTS = {
    "Aadhaar Card": [
        "Identity Proof",
        "Address Proof",
        "Date of Birth Proof"
    ],
    "PAN Card": [
        "Identity Proof",
        "Address Proof",
        "Date of Birth Proof"
    ],
    "Voter ID Card": [
        "Identity Proof",
        "Address Proof",
        "Age / Date of Birth Proof"
    ],
    "Passport": [
        "Identity Proof",
        "Address Proof",
        "Date of Birth Proof"
    ],
    "Driving Licence": [
        "Identity Proof",
        "Address Proof",
        "Age / Date of Birth Proof"
    ],
    "Birth Certificate": [
        "Identity Proof",
        "Birth Record / Supporting Proof"
    ],
    "Death Certificate": [
        "Identity Proof",
        "Death Record / Supporting Proof"
    ],
    "Caste Certificate": [
        "Identity Proof",
        "Address Proof",
        "Supporting Caste Documents"
    ],
    "Caste Validity Certificate": [
        "Caste Certificate",
        "Identity Proof",
        "Supporting Caste Documents"
    ],
    "Income Certificate": [
        "Identity Proof",
        "Address Proof",
        "Income Supporting Document"
    ],
    "Non-Creamy Layer Certificate": [
        "Income Proof",
        "Caste Certificate",
        "Identity Proof",
        "Address Proof"
    ],
    "EWS Certificate": [
        "Identity Proof",
        "Address Proof",
        "Income / Asset Proof"
    ],
    "Domicile Certificate": [
        "Identity Proof",
        "Address Proof",
        "Residence Supporting Document"
    ],
    "Residence Certificate": [
        "Identity Proof",
        "Address Proof",
        "Residence Supporting Document"
    ],
    "Nationality Certificate": [
        "Identity Proof",
        "Address Proof",
        "Nationality Supporting Proof"
    ],
    "Ration Card": [
        "Identity Proof",
        "Address Proof",
        "Family Details"
    ],
    "Disability Certificate / UDID": [
        "Identity Proof",
        "Disability / Medical Supporting Document"
    ],
    "Senior Citizen Certificate": [
        "Identity Proof",
        "Age Proof",
        "Address Proof"
    ],
    "Marriage Certificate": [
        "Identity Proof",
        "Address Proof",
        "Marriage Supporting Documents"
    ],
    "Legal Heir Certificate": [
        "Identity Proof",
        "Address Proof",
        "Relationship / Legal Supporting Documents"
    ],
    "Character Certificate": [
        "Identity Proof",
        "Address Proof",
        "Character Verification / Supporting Proof"
    ],
    "Solvency Certificate": [
        "Identity Proof",
        "Address Proof",
        "Financial Supporting Documents"
    ],
    "Land / 7-12 Extract": [
        "Identity Proof",
        "Land Record / 7-12 Document"
    ],
    "Property Card": [
        "Identity Proof",
        "Property Record / Supporting Document"
    ]
}

# Documents that commonly have a date/validity period are suggested with expiry ON.
# The user can still switch expiry OFF for any document.
EXPIRY_SUGGESTED = {
    "Non-Creamy Layer Certificate",
    "Income Certificate",
    "EWS Certificate",
    "Domicile Certificate",
    "Residence Certificate",
    "Caste Validity Certificate",
    "Driving Licence",
    "Passport",
    "Character Certificate",
    "Solvency Certificate",
    "Disability Certificate / UDID",
    "Senior Citizen Certificate"
}

# =========================================================
# PASSWORD / EXPIRY HELPERS
# =========================================================
def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def check_password(password, password_hash):
    return hash_password(password) == password_hash


def expiry_status(expiry_date):
    if not expiry_date:
        return "⚪ No Expiry", None

    try:
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d").date()
        days = (expiry - date.today()).days

        if days < 0:
            return "🔴 Expired", days
        if days <= 30:
            return "🟡 Expiring Soon", days
        return "🟢 Valid", days
    except (ValueError, TypeError):
        return "⚪ No Expiry", None


def expiry_text(expiry_date):
    status, days = expiry_status(expiry_date)
    if days is None:
        return status
    if days >= 0:
        return f"{status} — {days} days remaining"
    return f"{status} — expired {abs(days)} days ago"


# =========================================================
# SESSION
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "user_name" not in st.session_state:
    st.session_state.user_name = None

# =========================================================
# REGISTER
# =========================================================
def register_page():
    st.title("🔐 Create Account")
    st.write("Create your Digital Legacy Manager account.")

    with st.form("register_form"):
        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Create Account", use_container_width=True)

        if submitted:
            if not all([name.strip(), email.strip(), password, confirm_password]):
                st.error("Please fill all fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif len(password) < 6:
                st.error("Password must contain at least 6 characters.")
            else:
                db = get_db()
                try:
                    db.execute(
                        "INSERT INTO users (name,email,password_hash) VALUES (?,?,?)",
                        (name.strip(), email.strip().lower(), hash_password(password))
                    )
                    db.commit()
                    st.success("Account created successfully. Please login.")
                except sqlite3.IntegrityError:
                    st.error("This email is already registered.")
                finally:
                    db.close()

# =========================================================
# LOGIN
# =========================================================
def login_page():
    st.title("🔑 Login")
    st.write("Login to your Digital Legacy Manager.")

    with st.form("login_form"):
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            db = get_db()
            user = db.execute(
                "SELECT * FROM users WHERE email = ?",
                (email.strip().lower(),)
            ).fetchone()
            db.close()

            if user and check_password(password, user["password_hash"]):
                st.session_state.logged_in = True
                st.session_state.user_id = user["id"]
                st.session_state.user_name = user["name"]
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid email or password.")

# =========================================================
# DASHBOARD
# =========================================================
def dashboard_page():
    st.title("🏠 Digital Legacy Manager")
    st.subheader(f"Welcome, {st.session_state.user_name} 👋")

    db = get_db()
    uid = st.session_state.user_id

    legacy_count = db.execute(
        "SELECT COUNT(*) FROM legacy_items WHERE user_id=?", (uid,)
    ).fetchone()[0]
    contact_count = db.execute(
        "SELECT COUNT(*) FROM contacts WHERE user_id=?", (uid,)
    ).fetchone()[0]
    document_count = db.execute(
        "SELECT COUNT(*) FROM documents WHERE user_id=?", (uid,)
    ).fetchone()[0]

    gov_uploaded = db.execute(
        """SELECT COUNT(*) FROM government_documents
           WHERE user_id=? AND status='Uploaded'""", (uid,)
    ).fetchone()[0]

    gov_expiring = 0
    gov_expired = 0
    gov_rows = db.execute(
        """SELECT expiry_date FROM government_documents
           WHERE user_id=? AND expiry_date IS NOT NULL""", (uid,)
    ).fetchall()
    db.close()

    for row in gov_rows:
        _, days = expiry_status(row["expiry_date"])
        if days is not None:
            if days < 0:
                gov_expired += 1
            elif days <= 30:
                gov_expiring += 1

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Digital Legacy", legacy_count)
    c2.metric("Emergency Contacts", contact_count)
    c3.metric("Documents", document_count)
    c4.metric("Gov. Documents", gov_uploaded)

    st.divider()

    if gov_expiring:
        st.warning(f"⚠️ {gov_expiring} government document(s) are expiring within 30 days.")
    if gov_expired:
        st.error(f"🔴 {gov_expired} government document(s) have expired.")

    st.info(
        "Digital Legacy Manager helps you organize digital information, "
        "emergency contacts, important documents and government documents."
    )

# =========================================================
# DIGITAL LEGACY
# =========================================================
def legacy_page():
    st.title("📦 Digital Legacy")
    uid = st.session_state.user_id

    with st.form("legacy_form"):
        title = st.text_input("Title", placeholder="Example: Important Online Accounts")
        description = st.text_area("Description")
        submitted = st.form_submit_button("Add Legacy Information", use_container_width=True)

        if submitted:
            if not title.strip():
                st.error("Please enter a title.")
            else:
                db = get_db()
                db.execute(
                    "INSERT INTO legacy_items (user_id,title,description) VALUES (?,?,?)",
                    (uid, title.strip(), description)
                )
                db.commit()
                db.close()
                st.success("Legacy information added successfully.")
                st.rerun()

    st.divider()
    db = get_db()
    rows = db.execute(
        "SELECT * FROM legacy_items WHERE user_id=? ORDER BY id DESC", (uid,)
    ).fetchall()
    db.close()

    if not rows:
        st.info("No digital legacy information added yet.")
    else:
        for row in rows:
            with st.expander(f"📌 {row['title']}"):
                st.write(row["description"] or "No description.")
                st.caption(f"Created: {row['created_at']}")

# =========================================================
# EMERGENCY CONTACTS
# =========================================================
def contacts_page():
    st.title("🚨 Emergency Contacts")
    uid = st.session_state.user_id

    with st.form("contact_form"):
        name = st.text_input("Contact Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone Number")
        relationship = st.text_input("Relationship")
        submitted = st.form_submit_button("Add Emergency Contact", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Please enter contact name.")
            else:
                db = get_db()
                db.execute(
                    """INSERT INTO contacts
                       (user_id,name,email,phone,relationship)
                       VALUES (?,?,?,?,?)""",
                    (uid, name.strip(), email, phone, relationship)
                )
                db.commit()
                db.close()
                st.success("Emergency contact added successfully.")
                st.rerun()

    st.divider()
    db = get_db()
    rows = db.execute(
        "SELECT * FROM contacts WHERE user_id=? ORDER BY id DESC", (uid,)
    ).fetchall()
    db.close()

    if not rows:
        st.info("No emergency contacts added yet.")
    else:
        for row in rows:
            with st.expander(f"👤 {row['name']}"):
                st.write(f"**Email:** {row['email'] or 'Not provided'}")
                st.write(f"**Phone:** {row['phone'] or 'Not provided'}")
                st.write(f"**Relationship:** {row['relationship'] or 'Not provided'}")

# =========================================================
# NORMAL DOCUMENTS
# =========================================================
def documents_page():
    st.title("📄 Documents")
    uid = st.session_state.user_id

    uploaded_file = st.file_uploader(
        "Upload Important Document",
        type=["pdf", "doc", "docx", "txt", "jpg", "jpeg", "png"],
        key="normal_document_upload"
    )

    if uploaded_file and st.button("Upload Document", use_container_width=True):
        safe_filename = (
            f"{uid}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{uploaded_file.name}"
        )
        path = os.path.join(UPLOAD_FOLDER, safe_filename)
        with open(path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        db = get_db()
        db.execute(
            """INSERT INTO documents
               (user_id,filename,original_filename)
               VALUES (?,?,?)""",
            (uid, safe_filename, uploaded_file.name)
        )
        db.commit()
        db.close()
        st.success("Document uploaded successfully.")
        st.rerun()

    st.divider()
    db = get_db()
    rows = db.execute(
        "SELECT * FROM documents WHERE user_id=? ORDER BY id DESC", (uid,)
    ).fetchall()
    db.close()

    if not rows:
        st.info("No documents uploaded yet.")
    else:
        for row in rows:
            path = os.path.join(UPLOAD_FOLDER, row["filename"])
            st.write(f"📄 **{row['original_filename']}**")
            if os.path.exists(path):
                with open(path, "rb") as f:
                    st.download_button(
                        "⬇️ Download",
                        data=f.read(),
                        file_name=row["original_filename"],
                        key=f"normal_download_{row['id']}"
                    )
            st.divider()

# =========================================================
# EMERGENCY INFORMATION
# =========================================================
def emergency_information_page():
    st.title("🩺 Emergency Information")
    uid = st.session_state.user_id

    db = get_db()
    existing = db.execute(
        "SELECT * FROM emergency_information WHERE user_id=?", (uid,)
    ).fetchone()
    db.close()

    values = {
        "blood_group": existing["blood_group"] if existing else "",
        "allergies": existing["allergies"] if existing else "",
        "medical_conditions": existing["medical_conditions"] if existing else "",
        "emergency_notes": existing["emergency_notes"] if existing else ""
    }

    with st.form("emergency_form"):
        blood_group = st.text_input("Blood Group", value=values["blood_group"] or "")
        allergies = st.text_area("Allergies", value=values["allergies"] or "")
        medical_conditions = st.text_area(
            "Medical Conditions", value=values["medical_conditions"] or ""
        )
        emergency_notes = st.text_area(
            "Emergency Notes", value=values["emergency_notes"] or ""
        )
        submitted = st.form_submit_button(
            "Save Emergency Information", use_container_width=True
        )

        if submitted:
            db = get_db()
            if existing:
                db.execute(
                    """UPDATE emergency_information
                       SET blood_group=?, allergies=?,
                           medical_conditions=?, emergency_notes=?
                       WHERE user_id=?""",
                    (blood_group, allergies, medical_conditions, emergency_notes, uid)
                )
            else:
                db.execute(
                    """INSERT INTO emergency_information
                       (user_id,blood_group,allergies,medical_conditions,emergency_notes)
                       VALUES (?,?,?,?,?)""",
                    (uid, blood_group, allergies, medical_conditions, emergency_notes)
                )
            db.commit()
            db.close()
            st.success("Emergency information saved successfully.")
            st.rerun()

# =========================================================
# GOVERNMENT DOCUMENTS
# =========================================================
def government_documents_page():
    st.title("🏛️ Government Documents")
    st.caption(
        "Organize required documents, upload files, verify them and track expiry dates."
    )

    uid = st.session_state.user_id

    # Ensure checklist rows exist for this user.
    db = get_db()
    for doc_type, requirements in GOVERNMENT_DOCUMENTS.items():
        for requirement in requirements:
            exists = db.execute(
                """SELECT id FROM government_documents
                   WHERE user_id=? AND document_type=? AND required_document=?""",
                (uid, doc_type, requirement)
            ).fetchone()
            if not exists:
                db.execute(
                    """INSERT INTO government_documents
                       (user_id,document_type,required_document)
                       VALUES (?,?,?)""",
                    (uid, doc_type, requirement)
                )
    db.commit()
    db.close()

    # -----------------------------------------------------
    # OVERALL SUMMARY
    # -----------------------------------------------------
    db = get_db()
    all_rows = db.execute(
        "SELECT * FROM government_documents WHERE user_id=? ORDER BY document_type,id",
        (uid,)
    ).fetchall()
    db.close()

    uploaded = sum(1 for r in all_rows if r["status"] == "Uploaded")
    missing = sum(1 for r in all_rows if r["status"] != "Uploaded")
    pending = sum(
        1 for r in all_rows
        if r["status"] == "Uploaded" and r["verification_status"] == "Pending"
    )
    verified = sum(
        1 for r in all_rows
        if r["status"] == "Uploaded" and r["verification_status"] == "Correct"
    )
    expiring = 0
    expired = 0

    for r in all_rows:
        if r["expiry_date"]:
            _, days = expiry_status(r["expiry_date"])
            if days is not None:
                if days < 0:
                    expired += 1
                elif days <= 30:
                    expiring += 1

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Uploaded", uploaded)
    s2.metric("Missing", missing)
    s3.metric("Pending Verification", pending)
    s4.metric("Verified Correct", verified)

    s5, s6 = st.columns(2)
    s5.metric("🟡 Expiring Soon", expiring)
    s6.metric("🔴 Expired", expired)

    if expiring:
        st.warning(f"⚠️ {expiring} document(s) are expiring within 30 days. Please update them.")
    if expired:
        st.error(f"🔴 {expired} document(s) have expired. Please update them.")

    st.divider()

    # -----------------------------------------------------
    # DOCUMENT SELECTOR
    # -----------------------------------------------------
    selected_type = st.selectbox(
        "📋 Select Government Document",
        list(GOVERNMENT_DOCUMENTS.keys()),
        key="gov_document_type"
    )

    requirements = GOVERNMENT_DOCUMENTS[selected_type]

    st.subheader(f"📄 {selected_type}")
    st.caption(
        "Actual requirements and validity periods can vary by issuing authority/state."
    )

    type_rows = [r for r in all_rows if r["document_type"] == selected_type]

    uploaded_type = sum(1 for r in type_rows if r["status"] == "Uploaded")
    pending_type = sum(
        1 for r in type_rows
        if r["status"] == "Uploaded" and r["verification_status"] == "Pending"
    )
    correct_type = sum(
        1 for r in type_rows
        if r["status"] == "Uploaded" and r["verification_status"] == "Correct"
    )
    missing_type = len(requirements) - uploaded_type

    a, b, c, d = st.columns(4)
    a.metric("Required", len(requirements))
    b.metric("Uploaded", uploaded_type)
    c.metric("Missing", missing_type)
    d.metric("Verified Correct", correct_type)

    st.divider()

    # -----------------------------------------------------
    # EACH REQUIRED DOCUMENT
    # -----------------------------------------------------
    for row in type_rows:
        rid = row["id"]
        title = row["required_document"]

        with st.container(border=True):
            st.markdown(f"### 📄 {title}")

            if row["status"] != "Uploaded":
                st.warning("⚠️ Not Uploaded")
            else:
                st.success(f"✓ Uploaded: {row['original_filename']}")

            # Existing verification state
            if row["status"] == "Uploaded":
                if row["verification_status"] == "Correct":
                    st.success("✅ Verification: Correct")
                elif row["verification_status"] == "Wrong":
                    st.error("❌ Verification: Wrong")
                    if row["verification_reason"]:
                        st.caption(f"Reason: {row['verification_reason']}")
                else:
                    st.info("⏳ Verification: Pending")

            # Expiry information
            if row["status"] == "Uploaded":
                if row["has_expiry"]:
                    st.write(f"📅 **Issue Date:** {row['issue_date'] or 'Not provided'}")
                    st.write(f"📅 **Expiry Date:** {row['expiry_date'] or 'Not provided'}")

                    if row["expiry_date"]:
                        status, days = expiry_status(row["expiry_date"])
                        if days is not None:
                            if days < 0:
                                st.error(f"🔴 Expired {abs(days)} days ago")
                            elif days <= 30:
                                st.warning(f"🟡 Expiring Soon — {days} days remaining")
                            else:
                                st.success(f"🟢 Valid — {days} days remaining")
                        else:
                            st.info(status)
                else:
                    st.info("⚪ No Expiry / Lifetime Validity")

                # Download current file
                if row["stored_filename"]:
                    path = os.path.join(UPLOAD_FOLDER, row["stored_filename"])
                    if os.path.exists(path):
                        with open(path, "rb") as f:
                            st.download_button(
                                "⬇️ Download Current Document",
                                data=f.read(),
                                file_name=row["original_filename"],
                                key=f"gov_download_{rid}"
                            )

            st.divider()

            # -------------------------------------------------
            # UPLOAD / REPLACE FORM
            # -------------------------------------------------
            st.markdown("#### 🔄 Upload / Replace")

            upload = st.file_uploader(
                "Choose file",
                type=["pdf", "jpg", "jpeg", "png", "doc", "docx"],
                key=f"gov_upload_{rid}"
            )

            default_expiry = selected_type in EXPIRY_SUGGESTED
            expiry_key = f"expiry_{rid}"

            has_expiry = st.checkbox(
                "☑ This document has an expiry date",
                value=bool(row["has_expiry"]) if row["status"] == "Uploaded" else default_expiry,
                key=expiry_key
            )

            issue_date = None
            expiry_date = None

            if has_expiry:
                old_issue = None
                old_expiry = None

                try:
                    if row["issue_date"]:
                        old_issue = datetime.strptime(
                            row["issue_date"], "%Y-%m-%d"
                        ).date()
                    if row["expiry_date"]:
                        old_expiry = datetime.strptime(
                            row["expiry_date"], "%Y-%m-%d"
                        ).date()
                except ValueError:
                    pass

                issue_date = st.date_input(
                    "📅 Issue Date",
                    value=old_issue or date.today(),
                    key=f"issue_{rid}"
                )

                expiry_date = st.date_input(
                    "📅 Expiry Date",
                    value=old_expiry or date.today(),
                    key=f"expire_{rid}"
                )

                if expiry_date <= issue_date:
                    st.error("Expiry Date must be after Issue Date.")

            save_label = "🔄 Update / Replace Document" if row["status"] == "Uploaded" else "⬆️ Upload Document"

            if st.button(save_label, key=f"save_gov_{rid}", use_container_width=True):
                if upload is None:
                    st.error("Please choose a file first.")
                elif has_expiry and expiry_date <= issue_date:
                    st.error("Please select a valid Expiry Date.")
                else:
                    safe_filename = (
                        f"{uid}_{rid}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_"
                        f"{upload.name}"
                    )
                    path = os.path.join(UPLOAD_FOLDER, safe_filename)

                    with open(path, "wb") as f:
                        f.write(upload.getbuffer())

                    # Remove old stored file after successful new upload.
                    old_path = None
                    if row["stored_filename"]:
                        old_path = os.path.join(UPLOAD_FOLDER, row["stored_filename"])

                    db = get_db()
                    db.execute(
                        """UPDATE government_documents
                           SET original_filename=?,
                               stored_filename=?,
                               status='Uploaded',
                               verification_status='Pending',
                               verification_reason=NULL,
                               uploaded_at=CURRENT_TIMESTAMP,
                               has_expiry=?,
                               issue_date=?,
                               expiry_date=?
                           WHERE id=? AND user_id=?""",
                        (
                            upload.name,
                            safe_filename,
                            1 if has_expiry else 0,
                            issue_date.isoformat() if has_expiry else None,
                            expiry_date.isoformat() if has_expiry else None,
                            rid,
                            uid
                        )
                    )
                    db.commit()
                    db.close()

                    if old_path and old_path != path and os.path.exists(old_path):
                        try:
                            os.remove(old_path)
                        except OSError:
                            pass

                    st.success("Document uploaded successfully and is now Pending Verification.")
                    st.rerun()

            # -------------------------------------------------
            # VERIFICATION
            # -------------------------------------------------
            if row["status"] == "Uploaded":
                st.markdown("#### 🔍 Verification")

                v1, v2 = st.columns(2)

                with v1:
                    if st.button("✅ Correct", key=f"correct_{rid}", use_container_width=True):
                        db = get_db()
                        db.execute(
                            """UPDATE government_documents
                               SET verification_status='Correct',
                                   verification_reason=NULL
                               WHERE id=? AND user_id=?""",
                            (rid, uid)
                        )
                        db.commit()
                        db.close()
                        st.success("Document marked as Correct.")
                        st.rerun()

                with v2:
                    if st.button("❌ Wrong", key=f"wrong_{rid}", use_container_width=True):
                        st.session_state[f"show_reason_{rid}"] = True
                        st.rerun()

                if st.session_state.get(f"show_reason_{rid}", False):
                    reason = st.text_input(
                        "Reason for wrong document",
                        key=f"reason_{rid}"
                    )
                    if st.button(
                        "Save Wrong Reason",
                        key=f"save_reason_{rid}",
                        use_container_width=True
                    ):
                        if not reason.strip():
                            st.error("Please enter a reason.")
                        else:
                            db = get_db()
                            db.execute(
                                """UPDATE government_documents
                                   SET verification_status='Wrong',
                                       verification_reason=?
                                   WHERE id=? AND user_id=?""",
                                (reason.strip(), rid, uid)
                            )
                            db.commit()
                            db.close()
                            st.session_state[f"show_reason_{rid}"] = False
                            st.success("Verification updated.")
                            st.rerun()

    st.divider()

    # -----------------------------------------------------
    # MY GOVERNMENT DOCUMENTS SUMMARY
    # -----------------------------------------------------
    st.subheader("📊 My Government Documents")

    db = get_db()
    summary_rows = db.execute(
        """SELECT * FROM government_documents
           WHERE user_id=? AND status='Uploaded'
           ORDER BY document_type, id""",
        (uid,)
    ).fetchall()
    db.close()

    if not summary_rows:
        st.info("No government documents uploaded yet.")
    else:
        for row in summary_rows:
            status, days = expiry_status(row["expiry_date"])
            with st.expander(f"📄 {row['document_type']} — {row['required_document']}"):
                st.write(f"**File:** {row['original_filename']}")
                st.write(f"**Verification:** {row['verification_status']}")
                if row["verification_reason"]:
                    st.write(f"**Reason:** {row['verification_reason']}")

                if row["has_expiry"]:
                    st.write(f"**Issue Date:** {row['issue_date'] or 'Not provided'}")
                    st.write(f"**Expiry Date:** {row['expiry_date'] or 'Not provided'}")
                    st.write(f"**Validity:** {expiry_text(row['expiry_date'])}")
                else:
                    st.write("**Validity:** ⚪ No Expiry / Lifetime Validity")

# =========================================================
# SETTINGS
# =========================================================
def settings_page():
    st.title("⚙️ Settings")
    st.write(f"**Name:** {st.session_state.user_name}")

    db = get_db()
    user = db.execute(
        "SELECT email FROM users WHERE id=?", (st.session_state.user_id,)
    ).fetchone()
    db.close()

    if user:
        st.write(f"**Email:** {user['email']}")

    st.divider()
    st.info("Your Digital Legacy Manager account is active.")

# =========================================================
# MAIN
# =========================================================
if not st.session_state.logged_in:
    st.sidebar.title("🔐 Digital Legacy Manager")
    menu = st.sidebar.radio("Menu", ["Login", "Create Account"])

    if menu == "Login":
        login_page()
    else:
        register_page()
else:
    st.sidebar.title("🔐 Digital Legacy Manager")
    st.sidebar.write(f"Welcome, {st.session_state.user_name}")
    st.sidebar.divider()

    menu = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Digital Legacy",
            "Emergency Contacts",
            "Documents",
            "Government Documents",
            "Emergency Information",
            "Settings"
        ]
    )

    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.user_name = None
        st.rerun()

    if menu == "Dashboard":
        dashboard_page()
    elif menu == "Digital Legacy":
        legacy_page()
    elif menu == "Emergency Contacts":
        contacts_page()
    elif menu == "Documents":
        documents_page()
    elif menu == "Government Documents":
        government_documents_page()
    elif menu == "Emergency Information":
        emergency_information_page()
    elif menu == "Settings":
        settings_page()
