import streamlit as st

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Digital Legacy Manager",
    page_icon="🔐",
    layout="wide"
)

# -----------------------------
# Session State
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_name" not in st.session_state:
    st.session_state.user_name = ""

if "email" not in st.session_state:
    st.session_state.email = ""

if "legacy" not in st.session_state:
    st.session_state.legacy = []

if "contacts" not in st.session_state:
    st.session_state.contacts = []

if "documents" not in st.session_state:
    st.session_state.documents = []


# -----------------------------
# Custom CSS
# -----------------------------
st.markdown("""
<style>

.main {
    background-color: #f5f3ff;
}

.title {
    text-align: center;
    color: #4c1d95;
    font-size: 42px;
    font-weight: bold;
}

.subtitle {
    text-align: center;
    color: #666666;
    font-size: 18px;
    margin-bottom: 30px;
}

.card {
    background-color: white;
    padding: 25px;
    border-radius: 15px;
    margin-bottom: 20px;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HOME PAGE
# ============================================================

if not st.session_state.logged_in:

    st.markdown(
        '<div class="title">🔐 Digital Legacy Manager</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Organize and manage your important digital information, '
        'documents and emergency contacts in one place.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.subheader("🌟 Key Features")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### 📁")
        st.write("**Digital Legacy**")
        st.write(
            "Organize important digital information "
            "and account details."
        )

    with col2:
        st.markdown("### 👨‍👩‍👧")
        st.write("**Emergency Contacts**")
        st.write(
            "Store trusted contacts for emergency situations."
        )

    with col3:
        st.markdown("### 📄")
        st.write("**Documents**")
        st.write(
            "Keep important document information organized."
        )

    with col4:
        st.markdown("### 💾")
        st.write("**Backup & Organization**")
        st.write(
            "Keep your important information organized."
        )

    st.markdown("---")

    st.subheader("🔐 Security Information")

    st.info(
        "This is a student project demonstration. "
        "Use sample information only. Do not enter real "
        "passwords, banking credentials or sensitive documents."
    )

    st.markdown("---")

    st.subheader("🚀 Get Started")

    with st.form("login_form"):

        name = st.text_input(
            "Your Name",
            placeholder="Enter your name"
        )

        email = st.text_input(
            "Email Address",
            placeholder="Enter your email"
        )

        submitted = st.form_submit_button(
            "Get Started 🔐",
            use_container_width=True
        )

        if submitted:

            if name and email:

                st.session_state.logged_in = True
                st.session_state.user_name = name
                st.session_state.email = email

                st.rerun()

            else:

                st.error(
                    "Please enter your name and email."
                )


# ============================================================
# LOGGED-IN APPLICATION
# ============================================================

else:

    # -------------------------
    # Sidebar
    # -------------------------

    st.sidebar.title("🔐 Digital Legacy Manager")

    st.sidebar.write(
        f"Welcome, **{st.session_state.user_name}**"
    )

    page = st.sidebar.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "📁 Digital Legacy",
            "👨‍👩‍👧 Emergency Contacts",
            "📄 Documents",
            "⚙️ Settings"
        ]
    )

    if st.sidebar.button("Logout"):

        st.session_state.logged_in = False
        st.rerun()


    # ========================================================
    # DASHBOARD
    # ========================================================

    if page == "🏠 Dashboard":

        st.title(
            f"Hello, {st.session_state.user_name} 👋"
        )

        st.write(
            "Welcome to your Digital Legacy Manager dashboard."
        )

        st.markdown("---")

        st.subheader("📊 Your Summary")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "📁 Legacy Items",
                len(st.session_state.legacy)
            )

        with col2:
            st.metric(
                "👨‍👩‍👧 Emergency Contacts",
                len(st.session_state.contacts)
            )

        with col3:
            st.metric(
                "📄 Documents",
                len(st.session_state.documents)
            )

        st.markdown("---")

        st.subheader("📌 Manage Your Digital Legacy")

        col1, col2 = st.columns(2)

        with col1:

            st.markdown(
                '<div class="card">'
                '<h3>📁 Digital Legacy</h3>'
                '<p>Manage important digital information.</p>'
                '</div>',
                unsafe_allow_html=True
            )

        with col2:

            st.markdown(
                '<div class="card">'
                '<h3>👨‍👩‍👧 Emergency Contacts</h3>'
                '<p>Manage trusted emergency contacts.</p>'
                '</div>',
                unsafe_allow_html=True
            )

        col3, col4 = st.columns(2)

        with col3:

            st.markdown(
                '<div class="card">'
                '<h3>📄 Documents</h3>'
                '<p>Organize important documents.</p>'
                '</div>',
                unsafe_allow_html=True
            )

        with col4:

            st.markdown(
                '<div class="card">'
                '<h3>⚙️ Settings</h3>'
                '<p>View account information.</p>'
                '</div>',
                unsafe_allow_html=True
            )


    # ========================================================
    # DIGITAL LEGACY
    # ========================================================

    elif page == "📁 Digital Legacy":

        st.title("📁 My Digital Legacy")

        st.write(
            "Add and manage important digital information."
        )

        st.markdown("---")

        with st.form("legacy_form"):

            title = st.text_input(
                "Title",
                placeholder="Example: Gmail Account"
            )

            category = st.selectbox(
                "Category",
                [
                    "Email",
                    "Social Media",
                    "Banking",
                    "Documents",
                    "Other"
                ]
            )

            description = st.text_area(
                "Description",
                placeholder="Enter important information"
            )

            save = st.form_submit_button(
                "Save Legacy",
                use_container_width=True
            )

            if save:

                if title and description:

                    st.session_state.legacy.append(
                        {
                            "title": title,
                            "category": category,
                            "description": description
                        }
                    )

                    st.success(
                        "Legacy information saved successfully!"
                    )

                else:

                    st.error(
                        "Please fill all required fields."
                    )

        st.markdown("---")

        st.subheader("📋 Saved Legacy Information")

        if st.session_state.legacy:

            for item in st.session_state.legacy:

                with st.container(border=True):

                    st.write(
                        f"### 📄 {item['title']}"
                    )

                    st.write(
                        f"**Category:** {item['category']}"
                    )

                    st.write(
                        item["description"]
                    )

        else:

            st.info(
                "No legacy information added yet."
            )


    # ========================================================
    # EMERGENCY CONTACTS
    # ========================================================

    elif page == "👨‍👩‍👧 Emergency Contacts":

        st.title("👨‍👩‍👧 Emergency Contacts")

        st.write(
            "Add trusted people who can be contacted in an emergency."
        )

        st.markdown("---")

        with st.form("contact_form"):

            contact_name = st.text_input(
                "Contact Name",
                placeholder="Example: Mother"
            )

            phone = st.text_input(
                "Phone Number",
                placeholder="Example: 9000000001"
            )

            relation = st.text_input(
                "Relation",
                placeholder="Example: Mother"
            )

            save_contact = st.form_submit_button(
                "Save Contact",
                use_container_width=True
            )

            if save_contact:

                if contact_name and phone and relation:

                    st.session_state.contacts.append(
                        {
                            "name": contact_name,
                            "phone": phone,
                            "relation": relation
                        }
                    )

                    st.success(
                        "Emergency contact saved successfully!"
                    )

                else:

                    st.error(
                        "Please fill all required fields."
                    )

        st.markdown("---")

        st.subheader("📋 Saved Contacts")

        if st.session_state.contacts:

            for contact in st.session_state.contacts:

                with st.container(border=True):

                    st.write(
                        f"### 👤 {contact['name']}"
                    )

                    st.write(
                        f"**Relation:** {contact['relation']}"
                    )

                    st.write(
                        f"📞 {contact['phone']}"
                    )

        else:

            st.info(
                "No emergency contacts added yet."
            )


    # ========================================================
    # DOCUMENTS
    # ========================================================

    elif page == "📄 Documents":

        st.title("📄 My Documents")

        st.write(
            "Add and organize important document information."
        )

        st.markdown("---")

        with st.form("document_form"):

            document_name = st.text_input(
                "Document Name",
                placeholder="Example: Degree Certificate"
            )

            document_type = st.selectbox(
                "Document Type",
                [
                    "Identity Document",
                    "Education",
                    "Financial",
                    "Medical",
                    "Legal",
                    "Other"
                ]
            )

            document_description = st.text_area(
                "Description",
                placeholder="Enter document information"
            )

            save_document = st.form_submit_button(
                "Save Document",
                use_container_width=True
            )

            if save_document:

                if document_name:

                    st.session_state.documents.append(
                        {
                            "name": document_name,
                            "type": document_type,
                            "description": document_description
                        }
                    )

                    st.success(
                        "Document information saved successfully!"
                    )

                else:

                    st.error(
                        "Please enter document name."
                    )

        st.markdown("---")

        st.subheader("📋 Saved Documents")

        if st.session_state.documents:

            for document in st.session_state.documents:

                with st.container(border=True):

                    st.write(
                        f"### 📄 {document['name']}"
                    )

                    st.write(
                        f"**Type:** {document['type']}"
                    )

                    if document["description"]:

                        st.write(
                            document["description"]
                        )

        else:

            st.info(
                "No documents added yet."
            )


    # ========================================================
    # SETTINGS
    # ========================================================

    elif page == "⚙️ Settings":

        st.title("⚙️ Settings")

        st.write(
            "Your Digital Legacy Manager account information."
        )

        st.markdown("---")

        st.subheader("👤 Profile Information")

        st.text_input(
            "Name",
            value=st.session_state.user_name,
            disabled=True
        )

        st.text_input(
            "Email",
            value=st.session_state.email,
            disabled=True
        )

        st.markdown("---")

        st.subheader("ℹ️ About This Project")

        st.write(
            "Digital Legacy Manager is a student project "
            "designed to help users organize digital information, "
            "emergency contacts and document details in one place."
        )

        st.info(
            "For demonstration purposes, use sample information only."
        )
