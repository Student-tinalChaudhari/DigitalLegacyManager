from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "digital_legacy_manager_secret_key"

DATABASE = "database.db"


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# --------------------------------------------------
# CREATE DATABASE TABLES
# --------------------------------------------------

def init_db():

    conn = get_db()
    cursor = conn.cursor()

    # USERS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # DIGITAL ASSETS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            asset_name TEXT NOT NULL,
            category TEXT,
            description TEXT,
            action TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # TRUSTED CONTACTS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trusted_contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            contact_name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            relationship TEXT,
            permission TEXT,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # LEGACY INSTRUCTIONS
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS legacy_instructions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            instruction TEXT NOT NULL,
            priority TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # EMERGENCY INFORMATION
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS emergency_information (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            emergency_name TEXT NOT NULL,
            emergency_phone TEXT,
            hospital TEXT,
            medical_notes TEXT,
            emergency_instructions TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return render_template("index.html")


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return "Please fill all required fields."

        if len(password) < 6:
            return "Password must contain at least 6 characters."

        hashed_password = generate_password_hash(password)

        conn = get_db()
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO users (name, email, password)
                VALUES (?, ?, ?)
            """, (name, email, hashed_password))

            conn.commit()

        except sqlite3.IntegrityError:

            conn.close()
            return "Email already registered. Please use another email."

        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        conn = get_db()

        user = conn.execute("""
            SELECT * FROM users
            WHERE email = ?
        """, (email,)).fetchone()

        if user:

            stored_password = user["password"]

            password_correct = False

            # New hashed passwords
            try:
                password_correct = check_password_hash(
                    stored_password,
                    password
                )
            except Exception:
                password_correct = False

            # Old plain-text passwords
            if not password_correct and stored_password == password:

                password_correct = True

                new_password = generate_password_hash(password)

                conn.execute("""
                    UPDATE users
                    SET password = ?
                    WHERE id = ?
                """, (new_password, user["id"]))

                conn.commit()

            if password_correct:

                session["user_id"] = user["id"]
                session["user_name"] = user["name"]

                conn.close()

                return redirect(url_for("dashboard"))

        conn.close()

        return "Invalid email or password."

    return render_template("login.html")


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()

    assets_count = conn.execute("""
        SELECT COUNT(*) FROM assets
        WHERE user_id = ?
    """, (user_id,)).fetchone()[0]

    contacts_count = conn.execute("""
        SELECT COUNT(*) FROM trusted_contacts
        WHERE user_id = ?
    """, (user_id,)).fetchone()[0]

    instructions_count = conn.execute("""
        SELECT COUNT(*) FROM legacy_instructions
        WHERE user_id = ?
    """, (user_id,)).fetchone()[0]

    emergency_count = conn.execute("""
        SELECT COUNT(*) FROM emergency_information
        WHERE user_id = ?
    """, (user_id,)).fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name"),
        assets_count=assets_count,
        contacts_count=contacts_count,
        instructions_count=instructions_count,
        emergency_count=emergency_count
    )


# ==================================================
# DIGITAL ASSETS
# ==================================================

@app.route("/assets", methods=["GET", "POST"])
def assets():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()

    if request.method == "POST":

        asset_name = request.form.get("asset_name", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        action = request.form.get("action", "").strip()

        if asset_name:

            conn.execute("""
                INSERT INTO assets
                (user_id, asset_name, category, description, action)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                asset_name,
                category,
                description,
                action
            ))

            conn.commit()

    search = request.args.get("search", "").strip()

    if search:

        assets_list = conn.execute("""
            SELECT * FROM assets
            WHERE user_id = ?
            AND (
                asset_name LIKE ?
                OR category LIKE ?
                OR description LIKE ?
            )
            ORDER BY id DESC
        """, (
            user_id,
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        )).fetchall()

    else:

        assets_list = conn.execute("""
            SELECT * FROM assets
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "assets.html",
        assets=assets_list,
        search=search
    )


# EDIT ASSET

@app.route("/edit_asset/<int:id>", methods=["GET", "POST"])
def edit_asset(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()

    asset = conn.execute("""
        SELECT * FROM assets
        WHERE id = ? AND user_id = ?
    """, (id, user_id)).fetchone()

    if not asset:
        conn.close()
        return "Asset not found."

    if request.method == "POST":

        asset_name = request.form.get("asset_name", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        action = request.form.get("action", "").strip()

        conn.execute("""
            UPDATE assets
            SET asset_name = ?,
                category = ?,
                description = ?,
                action = ?
            WHERE id = ? AND user_id = ?
        """, (
            asset_name,
            category,
            description,
            action,
            id,
            user_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("assets"))

    conn.close()

    return render_template(
        "edit_asset.html",
        asset=asset
    )


# DELETE ASSET

@app.route("/delete_asset/<int:id>")
def delete_asset(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute("""
        DELETE FROM assets
        WHERE id = ? AND user_id = ?
    """, (id, session["user_id"]))

    conn.commit()
    conn.close()

    return redirect(url_for("assets"))


# ==================================================
# TRUSTED CONTACTS
# ==================================================

@app.route("/trusted_contacts", methods=["GET", "POST"])
def trusted_contacts():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()

    if request.method == "POST":

        contact_name = request.form.get("contact_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        relationship = request.form.get("relationship", "").strip()
        permission = request.form.get("permission", "").strip()
        notes = request.form.get("notes", "").strip()

        if contact_name:

            conn.execute("""
                INSERT INTO trusted_contacts
                (
                    user_id,
                    contact_name,
                    email,
                    phone,
                    relationship,
                    permission,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                contact_name,
                email,
                phone,
                relationship,
                permission,
                notes
            ))

            conn.commit()

    search = request.args.get("search", "").strip()

    if search:

        contacts = conn.execute("""
            SELECT * FROM trusted_contacts
            WHERE user_id = ?
            AND (
                contact_name LIKE ?
                OR email LIKE ?
                OR relationship LIKE ?
            )
            ORDER BY id DESC
        """, (
            user_id,
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        )).fetchall()

    else:

        contacts = conn.execute("""
            SELECT * FROM trusted_contacts
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "trusted_contacts.html",
        contacts=contacts,
        search=search
    )


# EDIT CONTACT

@app.route("/edit_contact/<int:id>", methods=["GET", "POST"])
def edit_contact(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()

    contact = conn.execute("""
        SELECT * FROM trusted_contacts
        WHERE id = ? AND user_id = ?
    """, (id, user_id)).fetchone()

    if not contact:
        conn.close()
        return "Trusted contact not found."

    if request.method == "POST":

        contact_name = request.form.get("contact_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        relationship = request.form.get("relationship", "").strip()
        permission = request.form.get("permission", "").strip()
        notes = request.form.get("notes", "").strip()

        conn.execute("""
            UPDATE trusted_contacts
            SET contact_name = ?,
                email = ?,
                phone = ?,
                relationship = ?,
                permission = ?,
                notes = ?
            WHERE id = ? AND user_id = ?
        """, (
            contact_name,
            email,
            phone,
            relationship,
            permission,
            notes,
            id,
            user_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("trusted_contacts"))

    conn.close()

    return render_template(
        "edit_contact.html",
        contact=contact
    )


# DELETE CONTACT

@app.route("/delete_contact/<int:id>")
def delete_contact(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute("""
        DELETE FROM trusted_contacts
        WHERE id = ? AND user_id = ?
    """, (id, session["user_id"]))

    conn.commit()
    conn.close()

    return redirect(url_for("trusted_contacts"))


# ==================================================
# LEGACY INSTRUCTIONS
# ==================================================

@app.route("/legacy_instructions", methods=["GET", "POST"])
def legacy_instructions():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        instruction = request.form.get("instruction", "").strip()
        priority = request.form.get("priority", "").strip()

        if title and instruction:

            conn.execute("""
                INSERT INTO legacy_instructions
                (
                    user_id,
                    title,
                    instruction,
                    priority
                )
                VALUES (?, ?, ?, ?)
            """, (
                user_id,
                title,
                instruction,
                priority
            ))

            conn.commit()

    search = request.args.get("search", "").strip()

    if search:

        instructions = conn.execute("""
            SELECT * FROM legacy_instructions
            WHERE user_id = ?
            AND (
                title LIKE ?
                OR instruction LIKE ?
                OR priority LIKE ?
            )
            ORDER BY id DESC
        """, (
            user_id,
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        )).fetchall()

    else:

        instructions = conn.execute("""
            SELECT * FROM legacy_instructions
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "legacy_instructions.html",
        instructions=instructions,
        search=search
    )


# EDIT INSTRUCTION

@app.route("/edit_instruction/<int:id>", methods=["GET", "POST"])
def edit_instruction(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()

    instruction = conn.execute("""
        SELECT * FROM legacy_instructions
        WHERE id = ? AND user_id = ?
    """, (id, user_id)).fetchone()

    if not instruction:
        conn.close()
        return "Instruction not found."

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        instruction_text = request.form.get("instruction", "").strip()
        priority = request.form.get("priority", "").strip()

        conn.execute("""
            UPDATE legacy_instructions
            SET title = ?,
                instruction = ?,
                priority = ?
            WHERE id = ? AND user_id = ?
        """, (
            title,
            instruction_text,
            priority,
            id,
            user_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("legacy_instructions"))

    conn.close()

    return render_template(
        "edit_instruction.html",
        instruction=instruction
    )


# DELETE INSTRUCTION

@app.route("/delete_instruction/<int:id>")
def delete_instruction(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute("""
        DELETE FROM legacy_instructions
        WHERE id = ? AND user_id = ?
    """, (id, session["user_id"]))

    conn.commit()
    conn.close()

    return redirect(url_for("legacy_instructions"))


# ==================================================
# EMERGENCY INFORMATION
# ==================================================

@app.route("/emergency_information", methods=["GET", "POST"])
def emergency_information():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()

    if request.method == "POST":

        emergency_name = request.form.get(
            "emergency_name", ""
        ).strip()

        emergency_phone = request.form.get(
            "emergency_phone", ""
        ).strip()

        hospital = request.form.get(
            "hospital", ""
        ).strip()

        medical_notes = request.form.get(
            "medical_notes", ""
        ).strip()

        emergency_instructions = request.form.get(
            "emergency_instructions", ""
        ).strip()

        if emergency_name:

            conn.execute("""
                INSERT INTO emergency_information
                (
                    user_id,
                    emergency_name,
                    emergency_phone,
                    hospital,
                    medical_notes,
                    emergency_instructions
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                emergency_name,
                emergency_phone,
                hospital,
                medical_notes,
                emergency_instructions
            ))

            conn.commit()

    search = request.args.get("search", "").strip()

    if search:

        emergencies = conn.execute("""
            SELECT * FROM emergency_information
            WHERE user_id = ?
            AND (
                emergency_name LIKE ?
                OR emergency_phone LIKE ?
                OR hospital LIKE ?
                OR medical_notes LIKE ?
            )
            ORDER BY id DESC
        """, (
            user_id,
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        )).fetchall()

    else:

        emergencies = conn.execute("""
            SELECT * FROM emergency_information
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "emergency_information.html",
        emergencies=emergencies,
        search=search
    )


# EDIT EMERGENCY

@app.route("/edit_emergency/<int:id>", methods=["GET", "POST"])
def edit_emergency(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    conn = get_db()

    emergency = conn.execute("""
        SELECT * FROM emergency_information
        WHERE id = ? AND user_id = ?
    """, (id, user_id)).fetchone()

    if not emergency:
        conn.close()
        return "Emergency information not found."

    if request.method == "POST":

        emergency_name = request.form.get(
            "emergency_name", ""
        ).strip()

        emergency_phone = request.form.get(
            "emergency_phone", ""
        ).strip()

        hospital = request.form.get(
            "hospital", ""
        ).strip()

        medical_notes = request.form.get(
            "medical_notes", ""
        ).strip()

        emergency_instructions = request.form.get(
            "emergency_instructions", ""
        ).strip()

        conn.execute("""
            UPDATE emergency_information
            SET emergency_name = ?,
                emergency_phone = ?,
                hospital = ?,
                medical_notes = ?,
                emergency_instructions = ?
            WHERE id = ? AND user_id = ?
        """, (
            emergency_name,
            emergency_phone,
            hospital,
            medical_notes,
            emergency_instructions,
            id,
            user_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("emergency_information"))

    conn.close()

    return render_template(
        "edit_emergency.html",
        emergency=emergency
    )


# DELETE EMERGENCY

@app.route("/delete_emergency/<int:id>")
def delete_emergency(id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    conn.execute("""
        DELETE FROM emergency_information
        WHERE id = ? AND user_id = ?
    """, (id, session["user_id"]))

    conn.commit()
    conn.close()

    return redirect(url_for("emergency_information"))


# ==================================================
# LOGOUT
# ==================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# ==================================================
# RUN APPLICATION
# ==================================================

if __name__ == "__main__":

    init_db()

    app.run(debug=True)