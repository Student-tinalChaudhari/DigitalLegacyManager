import os
import sqlite3
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file
)

from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet


# =========================================================
# APP CONFIGURATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "digital-legacy-manager-secret-key-change-in-render"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "database.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================================================
# ENCRYPTION KEY
# =========================================================

def get_encryption_key():
    key = os.environ.get("ENCRYPTION_KEY")

    if key:
        return key.encode()

    key_file = os.path.join(BASE_DIR, "encryption.key")

    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            return f.read()

    new_key = Fernet.generate_key()

    try:
        with open(key_file, "wb") as f:
            f.write(new_key)
    except Exception:
        pass

    return new_key


ENCRYPTION_KEY = get_encryption_key()
fernet = Fernet(ENCRYPTION_KEY)


# =========================================================
# DATABASE
# =========================================================

def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():

    db = get_db()

    # Users
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    # Digital Legacy
    db.execute("""
        CREATE TABLE IF NOT EXISTS legacy_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Contacts
    db.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            relationship TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Documents
    db.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.commit()
    db.close()


create_tables()


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(view_function):

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        if "user" not in session:
            flash("Please login to continue.")
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return wrapped_view


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    if "user" in session:
        return redirect(url_for("dashboard"))

    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password:
            flash("Please fill all required fields.")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        db = get_db()

        try:

            db.execute(
                """
                INSERT INTO users
                (name, email, password_hash)
                VALUES (?, ?, ?)
                """,
                (name, email, password_hash)
            )

            db.commit()

            flash("Registration successful. Please login.")

        except sqlite3.IntegrityError:

            flash("Email already registered.")

        finally:

            db.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()

        user = db.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        db.close()

        if user and check_password_hash(
            user["password_hash"],
            password
        ):

            session.clear()

            session["user"] = user["name"]
            session["email"] = user["email"]
            session["user_id"] = user["id"]

            flash("Login successful.")

            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")

    return render_template("login.html")


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    user_id = session["user_id"]

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

    contacts = db.execute(
        """
        SELECT *
        FROM contacts
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

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

    return render_template(
        "dashboard.html",
        user=session["user"],
        items=items,
        contacts=contacts,
        documents=documents
    )


# =========================================================
# DIGITAL LEGACY
# =========================================================

@app.route("/legacy")
@login_required
def legacy():

    user_id = session["user_id"]

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

    return render_template(
        "legacy_instructions.html",
        items=items
    )


@app.route("/legacy/add", methods=["POST"])
@login_required
def add_legacy():

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()

    if not title:
        flash("Title is required.")
        return redirect(url_for("legacy"))

    db = get_db()

    db.execute(
        """
        INSERT INTO legacy_items
        (user_id, title, description)
        VALUES (?, ?, ?)
        """,
        (
            session["user_id"],
            title,
            description
        )
    )

    db.commit()
    db.close()

    flash("Legacy information added successfully.")

    return redirect(url_for("legacy"))


# =========================================================
# CONTACTS
# =========================================================

@app.route("/contacts")
@login_required
def contacts():

    user_id = session["user_id"]

    db = get_db()

    contact_list = db.execute(
        """
        SELECT *
        FROM contacts
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    db.close()

    return render_template(
        "trusted_contacts.html",
        contacts=contact_list
    )


@app.route("/contacts/add", methods=["POST"])
@login_required
def add_contact():

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    relationship = request.form.get(
        "relationship",
        ""
    ).strip()

    if not name:
        flash("Contact name is required.")
        return redirect(url_for("contacts"))

    db = get_db()

    db.execute(
        """
        INSERT INTO contacts
        (
            user_id,
            name,
            email,
            phone,
            relationship
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            session["user_id"],
            name,
            email,
            phone,
            relationship
        )
    )

    db.commit()
    db.close()

    flash("Emergency contact added successfully.")

    return redirect(url_for("contacts"))


# =========================================================
# DOCUMENTS
# =========================================================

@app.route("/documents")
@login_required
def documents():

    user_id = session["user_id"]

    db = get_db()

    document_list = db.execute(
        """
        SELECT *
        FROM documents
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    db.close()

    return render_template(
        "documents.html",
        documents=document_list
    )


@app.route("/documents/add", methods=["POST"])
@login_required
def add_document():

    uploaded_file = request.files.get("document")

    if not uploaded_file or not uploaded_file.filename:
        flash("Please select a document.")
        return redirect(url_for("documents"))

    original_filename = uploaded_file.filename

    safe_filename = (
        str(session["user_id"])
        + "_"
        + original_filename
        .replace("/", "_")
        .replace("\\", "_")
    )

    file_path = os.path.join(
        UPLOAD_FOLDER,
        safe_filename
    )

    try:

        file_data = uploaded_file.read()

        encrypted_data = fernet.encrypt(file_data)

        with open(file_path, "wb") as f:
            f.write(encrypted_data)

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
                session["user_id"],
                safe_filename,
                original_filename
            )
        )

        db.commit()
        db.close()

        flash("Document uploaded successfully.")

    except Exception as error:

        print("Document upload error:", error)
        flash("Unable to upload document.")

    return redirect(url_for("documents"))


@app.route("/documents/view/<int:document_id>")
@login_required
def view_document(document_id):

    db = get_db()

    document = db.execute(
        """
        SELECT *
        FROM documents
        WHERE id = ?
        AND user_id = ?
        """,
        (
            document_id,
            session["user_id"]
        )
    ).fetchone()

    db.close()

    if not document:
        flash("Document not found.")
        return redirect(url_for("documents"))

    file_path = os.path.join(
        UPLOAD_FOLDER,
        document["filename"]
    )

    if not os.path.exists(file_path):
        flash("Document file not found.")
        return redirect(url_for("documents"))

    try:

        with open(file_path, "rb") as f:
            encrypted_data = f.read()

        decrypted_data = fernet.decrypt(
            encrypted_data
        )

        temp_file = os.path.join(
            UPLOAD_FOLDER,
            "temp_" + document["original_filename"]
        )

        with open(temp_file, "wb") as f:
            f.write(decrypted_data)

        return send_file(
            temp_file,
            as_attachment=False,
            download_name=document["original_filename"]
        )

    except Exception as error:

        print("Document view error:", error)

        flash("Unable to open document.")

        return redirect(url_for("documents"))


@app.route("/documents/delete/<int:document_id>", methods=["POST"])
@login_required
def delete_document(document_id):

    db = get_db()

    document = db.execute(
        """
        SELECT *
        FROM documents
        WHERE id = ?
        AND user_id = ?
        """,
        (
            document_id,
            session["user_id"]
        )
    ).fetchone()

    if not document:

        db.close()

        flash("Document not found.")

        return redirect(url_for("documents"))

    file_path = os.path.join(
        UPLOAD_FOLDER,
        document["filename"]
    )

    if os.path.exists(file_path):

        try:
            os.remove(file_path)
        except Exception:
            pass

    db.execute(
        """
        DELETE FROM documents
        WHERE id = ?
        AND user_id = ?
        """,
        (
            document_id,
            session["user_id"]
        )
    )

    db.commit()
    db.close()

    flash("Document deleted successfully.")

    return redirect(url_for("documents"))


# =========================================================
# SETTINGS
# =========================================================

@app.route("/settings")
@login_required
def settings():

    db = get_db()

    user = db.execute(
        """
        SELECT id, name, email
        FROM users
        WHERE id = ?
        """,
        (session["user_id"],)
    ).fetchone()

    db.close()

    return render_template(
        "settings.html",
        user=user
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash("You have been logged out.")

    return redirect(url_for("login"))


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )