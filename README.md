# Digital Legacy Manager

Digital Legacy Manager is a web-based application developed using Python, Streamlit, and SQLite.

It helps users securely organize and manage important digital information, government documents, trusted contacts, legacy instructions, and emergency information in one place.

## Features

- User Registration and Login
- Dashboard
- Digital Legacy Management
- Emergency Contact Management
- Document Management
- Government Document Management
- Government Document Upload and Replace
- Document Download
- Document Verification
- Wrong Document Verification with Reason
- Issue Date and Expiry Date Tracking
- Expiry Alerts
- Emergency Information Management
- Add, View, Update and Delete Records
- SQLite Database

## Main Modules

### 1. Digital Legacy

Users can store and manage important digital legacy information in one place.

### 2. Emergency Contacts

Users can add trusted emergency contacts along with their name, email, phone number, and relationship.

### 3. Documents

Users can upload and manage their important personal documents.

### 4. Government Documents

Users can select different government documents and manage their required-document checklist.

The module supports:

- Document Upload
- Document Replace / Update
- Document Download
- Correct / Wrong Verification
- Verification Reason
- Issue Date
- Expiry Date
- Days Remaining
- Expired Document Status
- Expiring Soon Alerts
- No Expiry / Lifetime Validity

### 5. Emergency Information

Users can store important emergency information such as:

- Blood Group
- Allergies
- Medical Conditions
- Emergency Notes

### 6. Settings

Users can manage application-related settings from the Settings section.

## Government Documents Supported

The application provides document management for various government and personal certificates, including:

- Aadhaar Card
- PAN Card
- Voter ID Card
- Passport
- Driving Licence
- Birth Certificate
- Caste Certificate
- Caste Validity Certificate
- Income Certificate
- Non-Creamy Layer Certificate
- EWS Certificate
- Domicile Certificate
- Residence Certificate
- Nationality Certificate
- Disability Certificate / UDID
- Senior Citizen Certificate
- Marriage Certificate
- Legal Heir Certificate
- Character Certificate
- Solvency Certificate
- Land / 7-12 Extract
- Property Card
- Ration Card
- Death Certificate

## Technologies Used

- Python
- Streamlit
- SQLite

## Database

The application uses SQLite to store user accounts and application data.

The database is created locally when the application runs.

## Project Structure

```text
DigitalLegacyManager/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── screenshots/
