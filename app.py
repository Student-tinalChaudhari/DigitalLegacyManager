from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    flash
)

import os
import uuid
import sqlite3
import io
import smtplib
from email.message import EmailMessage
from functools import wraps

from cryptography.fernet import Fernet

from werkzeug.utils import secure_filename
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# =========================================================
# APP
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "digital-legacy-manager-local-demo-secret-2026"
)


# =========================================================
# DATABASE
# =========================================================

DATABASE = "database.db"


def get_db_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# ENCRYPTION KEY
# =========================================================

KEY_FILE = "encryption.key"


def load_encryption_key():

    environment_key = os.environ.get(
        "ENCRYPTION_KEY"
    )

    if environment_key:

        try:
            return environment_key.encode()

        except Exception:
            pass

    if os.path.exists(KEY_FILE):

        with open(
            KEY_FILE,
            "rb"
        ) as key_file:

            key = key_file.read()

        try:

            Fernet(key)

            return key

        except Exception:
            pass

    new_key = Fernet.generate_key()

    with open(
        KEY_FILE,
        "wb"
    ) as key_file:

        key_file.write(new_key)

    return new_key


ENCRYPTION_KEY = load_encryption_key()

fernet = Fernet(
    ENCRYPTION_KEY
)


# =========================================================
# UPLOAD SETTINGS
# =========================================================

UPLOAD_FOLDER = "uploads"

ALLOWED_EXTENSIONS = {
    "pdf",
    "jpg",
    "jpeg",
    "png"
}

MAX_FILE_SIZE = 10 * 1024 * 1024

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# =========================================================
# TEMPORARY DATA
# =========================================================

legacy_items = []

emergency_contacts = []


# =========================================================
# EMAIL SETTINGS
# =========================================================

SMTP_HOST = os.environ.get(
    "SMTP_HOST"
)

SMTP_PORT = os.environ.get(
    "SMTP_PORT",
    "587"
)

SMTP_USERNAME = os.environ.get(
    "SMTP_USERNAME"
)

SMTP_PASSWORD = os.environ.get(
    "SMTP_PASSWORD"
)

NOTIFICATION_FROM = os.environ.get(
    "NOTIFICATION_FROM",
    SMTP_USERNAME
)


def send_email_notification(
    recipient,
    subject,
    message
):

    if not all([
        SMTP_HOST,
        SMTP_USERNAME,
        SMTP_PASSWORD,
        recipient
    ]):

        print(
            "Email notification skipped: SMTP not configured."
        )

        return False

    try:

        email = EmailMessage()

        email["From"] = NOTIFICATION_FROM

        email["To"] = recipient

        email["Subject"] = subject

        email.set_content(
            message
        )

        with smtplib.SMTP(
            SMTP_HOST,
            int(SMTP_PORT)
        ) as server:

            server.starttls()

            server.login(
                SMTP_USERNAME,
                SMTP_PASSWORD
            )

            server.send_message(
                email
            )

        print(
            "Email notification sent."
        )

        return True

    except Exception as error:

        print(
            "Email notification failed:",
            error
        )

        return False


# =========================================================
# USERS TABLE
# =========================================================

def create_users_table():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password_hash TEXT NOT NULL,

            two_factor_secret TEXT,

            two_factor_enabled INTEGER DEFAULT 0,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()

    connection.close()


# =========================================================
# DOCUMENTS TABLE
# =========================================================

def create_documents_table():

    connection = get_db_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_email TEXT NOT NULL,

            name TEXT NOT NULL,

            document_type TEXT NOT NULL,

            description TEXT,

            original_filename TEXT NOT NULL,

            stored_filename TEXT NOT NULL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()

    connection.close()


# =========================================================
# FILE VALIDATION
# =========================================================

def allowed_file(filename):

    return (
        "."
        in filename
        and
        filename.rsplit(
            ".",
            1
        )[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(view_function):

    @wraps(view_function)
    def wrapped_view(
        *args,
        **kwargs
    ):

        if "user" not in session:

            flash(
                "Please login to continue."
            )

            return redirect(
                url_for("login")
            )

        return view_function(
            *args,
            **kwargs
        )

    return wrapped_view


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not name or not email or not password:

            flash(
                "Please fill all required fields."
            )

            return redirect(
                url_for("register")
            )

        if len(password) < 8:

            flash(
                "Password must contain at least 8 characters."
            )

            return redirect(
                url_for("register")
            )

        if password != confirm_password:

            flash(
                "Passwords do not match."
            )

            return redirect(
                url_for("register")
            )

        connection = get_db_connection()

        existing_user = connection.execute(
            """
            SELECT id
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        if existing_user:

            connection.close()

            flash(
                "An account with this email already exists."
            )

            return redirect(
                url_for("register")
            )

        password_hash = generate_password_hash(
            password
        )

        connection.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password_hash
            )
            VALUES (?, ?, ?)
            """,
            (
                name,
                email,
                password_hash
            )
        )

        connection.commit()

        connection.close()

        send_email_notification(
            email,
            "Digital Legacy Manager - Account Created",
            f"""
Hello {name},

Your Digital Legacy Manager account has been created successfully.

Thank you,
Digital Legacy Manager
"""
        )

        flash(
            "Account created successfully. Please login."
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        connection = get_db_connection()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        connection.close()

        if not user:

            flash(
                "Invalid email or password."
            )

            return redirect(
                url_for("login")
            )

        if not check_password_hash(
            user["password_hash"],
            password
        ):

            flash(
                "Invalid email or password."
            )

            return redirect(
                url_for("login")
            )

        session.clear()

        session["user"] = user["name"]

        session["email"] = user["email"]

        send_email_notification(
            user["email"],
            "Digital Legacy Manager - New Login",
            f"""
Hello {user["name"]},

A successful login was completed on your Digital Legacy Manager account.

Thank you,
Digital Legacy Manager
"""
        )

        flash(
            "Login successful."
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "login.html"
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    connection = get_db_connection()

    document_count = connection.execute(
        """
        SELECT COUNT(*)
        FROM documents
        WHERE user_email = ?
        """,
        (session["email"],)
    ).fetchone()[0]

    connection.close()

    return render_template(
        "dashboard.html",
        user=session["user"],
        items=legacy_items,
        contacts=emergency_contacts,
        documents_count=document_count
    )


# =========================================================
# LEGACY
# =========================================================

@app.route("/legacy")
@login_required
def legacy():

    return render_template(
        "legacy_instructions.html",
        items=legacy_items
    )


@app.route(
    "/add-legacy",
    methods=["POST"]
)
@login_required
def add_legacy():

    title = request.form.get(
        "title",
        ""
    ).strip()

    instruction = request.form.get(
        "instruction",
        ""
    ).strip()

    if title and instruction:

        legacy_items.append(
            {
                "title": title,
                "instruction": instruction
            }
        )

        flash(
            "Legacy instruction added successfully."
        )

    return redirect(
        url_for("legacy")
    )


# =========================================================
# CONTACTS
# =========================================================

@app.route("/contacts")
@login_required
def contacts():

    return render_template(
        "trusted_contacts.html",
        contacts=emergency_contacts
    )


@app.route(
    "/add-contact",
    methods=["POST"]
)
@login_required
def add_contact():

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    if name:

        emergency_contacts.append(
            {
                "name": name,
                "email": email,
                "phone": phone
            }
        )

        flash(
            "Trusted contact added successfully."
        )

    return redirect(
        url_for("contacts")
    )


# =========================================================
# DOCUMENTS
# =========================================================

@app.route("/documents")
@login_required
def documents():

    connection = get_db_connection()

    documents_list = connection.execute(
        """
        SELECT *
        FROM documents
        WHERE user_email = ?
        ORDER BY id DESC
        """,
        (session["email"],)
    ).fetchall()

    connection.close()

    return render_template(
        "documents.html",
        documents=documents_list
    )


# =========================================================
# ADD DOCUMENT
# =========================================================

@app.route(
    "/add-document",
    methods=["POST"]
)
@login_required
def add_document():

    document_name = request.form.get(
        "document_name",
        ""
    ).strip()

    document_type = request.form.get(
        "document_type",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    document_file = request.files.get(
        "document_file"
    )

    if not document_name:

        flash(
            "Document name is required."
        )

        return redirect(
            url_for("documents")
        )

    if not document_type:

        flash(
            "Document type is required."
        )

        return redirect(
            url_for("documents")
        )

    if not document_file:

        flash(
            "Please select a document."
        )

        return redirect(
            url_for("documents")
        )

    if document_file.filename == "":

        flash(
            "Please select a document."
        )

        return redirect(
            url_for("documents")
        )

    if not allowed_file(
        document_file.filename
    ):

        flash(
            "Only PDF, JPG, JPEG and PNG files are allowed."
        )

        return redirect(
            url_for("documents")
        )

    original_filename = secure_filename(
        document_file.filename
    )

    original_data = document_file.read()

    if not original_data:

        flash(
            "The selected file is empty."
        )

        return redirect(
            url_for("documents")
        )

    encrypted_data = fernet.encrypt(
        original_data
    )

    stored_filename = (
        uuid.uuid4().hex
        + ".enc"
    )

    stored_path = os.path.join(
        UPLOAD_FOLDER,
        stored_filename
    )

    with open(
        stored_path,
        "wb"
    ) as encrypted_file:

        encrypted_file.write(
            encrypted_data
        )

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO documents
        (
            user_email,
            name,
            document_type,
            description,
            original_filename,
            stored_filename
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            session["email"],
            document_name,
            document_type,
            description,
            original_filename,
            stored_filename
        )
    )

    connection.commit()

    connection.close()

    send_email_notification(
        session["email"],
        "Digital Legacy Manager - Document Uploaded",
        f"""
Hello {session["user"]},

A new document was uploaded successfully.

Document:
{document_name}

Type:
{document_type}

The document is stored in encrypted form.

Thank you,
Digital Legacy Manager
"""
    )

    flash(
        "Document encrypted and uploaded successfully!"
    )

    return redirect(
        url_for("documents")
    )


# =========================================================
# VIEW DOCUMENT
# =========================================================

@app.route(
    "/document/<filename>"
)
@login_required
def view_document(filename):

    connection = get_db_connection()

    document = connection.execute(
        """
        SELECT *
        FROM documents
        WHERE stored_filename = ?
        AND user_email = ?
        """,
        (
            filename,
            session["email"]
        )
    ).fetchone()

    connection.close()

    if not document:

        flash(
            "Document not found or access denied."
        )

        return redirect(
            url_for("documents")
        )

    stored_path = os.path.join(
        UPLOAD_FOLDER,
        document["stored_filename"]
    )

    if not os.path.exists(
        stored_path
    ):

        flash(
            "Encrypted file not found."
        )

        return redirect(
            url_for("documents")
        )

    try:

        with open(
            stored_path,
            "rb"
        ) as encrypted_file:

            encrypted_data = encrypted_file.read()

        decrypted_data = fernet.decrypt(
            encrypted_data
        )

        return send_file(
            io.BytesIO(
                decrypted_data
            ),
            mimetype="application/octet-stream",
            as_attachment=False,
            download_name=document[
                "original_filename"
            ]
        )

    except Exception:

        flash(
            "Unable to decrypt the document."
        )

        return redirect(
            url_for("documents")
        )


# =========================================================
# DELETE DOCUMENT
# =========================================================

@app.route(
    "/delete-document/<filename>",
    methods=["POST"]
)
@login_required
def delete_document(filename):

    connection = get_db_connection()

    document = connection.execute(
        """
        SELECT *
        FROM documents
        WHERE stored_filename = ?
        AND user_email = ?
        """,
        (
            filename,
            session["email"]
        )
    ).fetchone()

    if not document:

        connection.close()

        flash(
            "Document not found or access denied."
        )

        return redirect(
            url_for("documents")
        )

    stored_path = os.path.join(
        UPLOAD_FOLDER,
        document["stored_filename"]
    )

    if os.path.exists(
        stored_path
    ):

        os.remove(
            stored_path
        )

    connection.execute(
        """
        DELETE FROM documents
        WHERE stored_filename = ?
        AND user_email = ?
        """,
        (
            filename,
            session["email"]
        )
    )

    connection.commit()

    connection.close()

    send_email_notification(
        session["email"],
        "Digital Legacy Manager - Document Deleted",
        f"""
Hello {session["user"]},

The following document was deleted:

{document["name"]}

Thank you,
Digital Legacy Manager
"""
    )

    flash(
        "Document deleted successfully."
    )

    return redirect(
        url_for("documents")
    )


# =========================================================
# SETTINGS
# =========================================================

@app.route("/settings")
@login_required
def settings():

    return render_template(
        "settings.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out successfully."
    )

    return redirect(
        url_for("login")
    )


# =========================================================
# INITIALIZE DATABASE
# =========================================================

create_users_table()

create_documents_table()


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )