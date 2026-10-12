# GovHospital Pulse - Citizen Feedback & Service Monitoring System

A comprehensive, responsive web application for citizens and patient families to evaluate the quality of services at local government hospitals. The portal collects structured public feedback on hospital care, hygiene, waiting times, and free medicine availability, and compiles it into a live performance analytics dashboard.

---

## 🌟 Complete Feature Set

1. **Citizen Feedback Form (`/`)**:
   - **Bilingual Support (English / हिन्दी)**: Instant one-click language toggle between English and Hindi.
   - **Hospital & Ward Selection**: Choose hospital name, department, date of visit, and emergency flag.
   - **5-Star Quality Ratings**:
     - Hospital Cleanliness & Hygiene
     - Doctor's Attention & Diagnosis
     - Nurses & Staff Courtesy
     - Waiting Queue & Registration
     - Overall Hospital Experience
   - **Essential Government Healthcare Services**:
     - Prescribed medicines provision (100% Free / Partially in stock / Bought outside)
     - Pathology & Diagnostic tests availability
     - Average wait duration (Under 30m to 2+ hours)
   - **Document & Evidence Upload**: Upload photos of medicine bills, out-of-stock slips, or prescriptions (JPG, PNG, WEBP, PDF up to 16MB).
   - **Anti-Corruption Audit Check**: Flag whether any unofficial payments or bribes were demanded.
   - **Citizen Privacy**: Full support for anonymous feedback or optional contact info.

2. **Printable Hospital Notice Board QR Poster (`/poster`)**:
   - Official A4-ready poster with a dynamically generated QR code pointing to the live portal.
   - Designed for printing and mounting on OPD registration queues, pharmacy counters, and hospital waiting rooms.
   - Bilingual instructions in English and Hindi.

3. **Admin Authentication & Protected Dashboard (`/dashboard`)**:
   - Protected by administrative login (`/login`).
   - Default Administrator Credentials:
     - **Username**: `admin`
     - **Password**: `hospital@admin123`
   - Real-time KPI summary cards (Average overall rating, Hygiene score, Doctor score, Free medicine delivery %, and total attached evidence files).
   - Department-wise satisfaction chart and medicine provision status doughnut chart.
   - One-click attachment preview for uploaded prescriptions or receipts.

4. **CSV Export (`/export/csv`)**:
   - Authenticated one-click download of all citizen submissions with file names for official audits and government reports.

---

## 🚀 How to Run the Application

### 1. Open Terminal in the Project Directory
```powershell
cd C:\Users\user\.gemini\antigravity\scratch\hospital_feedback_app
```

### 2. Start the Server
```powershell
python app.py
```

### 3. Open in Browser
- **Citizen Feedback Form**: [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **Printable QR Poster**: [http://127.0.0.1:5000/poster](http://127.0.0.1:5000/poster)
- **Admin Login**: [http://127.0.0.1:5000/login](http://127.0.0.1:5000/login) *(User: `admin` | Pass: `hospital@admin123`)*
- **Admin Dashboard**: [http://127.0.0.1:5000/dashboard](http://127.0.0.1:5000/dashboard)
- **Download Audit CSV**: [http://127.0.0.1:5000/export/csv](http://127.0.0.1:5000/export/csv)

---

## 📁 Project Structure
```text
hospital_feedback_app/
├── app.py                  # Flask backend, auth, SQLite schema, uploads & CSV export
├── hospital_feedback.db    # SQLite database
├── requirements.txt        # Python package requirements
├── README.md               # Complete documentation
├── static/
│   └── uploads/            # Secure citizen uploaded photos / prescriptions
└── templates/
    ├── base.html           # Layout with bilingual i18n switcher, Tailwind CSS, icons
    ├── index.html          # Public citizen feedback submission form with file upload
    ├── poster.html         # Printable A4 notice poster with dynamic QR code
    ├── login.html          # Administrator login portal
    ├── thank_you.html      # Submission confirmation with tracking reference code
    └── dashboard.html      # Performance audit dashboard with chart analytics
```
