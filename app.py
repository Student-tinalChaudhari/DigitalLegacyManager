from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "digital-legacy-manager-demo"

legacy_items = []
emergency_contacts = []
documents = []


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")

        if name and email:
            session["user"] = name
            session["email"] = email
            return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        user=session["user"],
        items=legacy_items,
        contacts=emergency_contacts,
        documents=documents
    )


@app.route("/legacy")
def legacy():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("legacy.html", items=legacy_items)


@app.route("/add-legacy", methods=["POST"])
def add_legacy():
    if "user" not in session:
        return redirect(url_for("login"))

    title = request.form.get("title")
    category = request.form.get("category")
    description = request.form.get("description")

    if title and category and description:
        legacy_items.append({
            "title": title,
            "category": category,
            "description": description
        })

    return redirect(url_for("legacy"))


@app.route("/contacts")
def contacts():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "contacts.html",
        contacts=emergency_contacts
    )


@app.route("/add-contact", methods=["POST"])
def add_contact():
    if "user" not in session:
        return redirect(url_for("login"))

    name = request.form.get("contact_name")
    phone = request.form.get("phone")
    relation = request.form.get("relation")

    if name and phone and relation:
        emergency_contacts.append({
            "name": name,
            "phone": phone,
            "relation": relation
        })

    return redirect(url_for("contacts"))


@app.route("/documents")
def documents_page():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "documents.html",
        documents=documents
    )


@app.route("/add-document", methods=["POST"])
def add_document():
    if "user" not in session:
        return redirect(url_for("login"))

    name = request.form.get("document_name")
    document_type = request.form.get("document_type")
    description = request.form.get("document_description")

    if name and document_type:
        documents.append({
            "name": name,
            "type": document_type,
            "description": description
        })

    return redirect(url_for("documents_page"))


@app.route("/settings")
def settings():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template(
        "settings.html",
        user=session["user"],
        email=session["email"]
    )


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
