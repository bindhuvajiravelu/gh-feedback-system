import os
import sqlite3
import csv
import io
import uuid
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, Response, session, send_from_directory
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "gov-hospital-feedback-secret-salt-key-2026"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "hospital_feedback.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Admin Credentials
ADMIN_USER = "admin"
ADMIN_PASS = "hospital@admin123"

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            hospital_name TEXT NOT NULL,
            department TEXT NOT NULL,
            visit_date TEXT,
            patient_type TEXT,
            is_emergency INTEGER DEFAULT 0,
            cleanliness_rating INTEGER NOT NULL,
            doctor_rating INTEGER NOT NULL,
            staff_courtesy_rating INTEGER NOT NULL,
            wait_time_rating INTEGER NOT NULL,
            overall_rating INTEGER NOT NULL,
            medicines_available TEXT NOT NULL,
            diagnostics_available TEXT NOT NULL,
            wait_time_duration TEXT,
            bribe_or_illegal_demand TEXT,
            comments TEXT,
            citizen_name TEXT,
            contact_number TEXT,
            attachment_filename TEXT
        )
    """)
    conn.commit()

    # Verify column existence in case table existed before
    cursor.execute("PRAGMA table_info(feedback)")
    columns = [row["name"] for row in cursor.fetchall()]
    if "attachment_filename" not in columns:
        cursor.execute("ALTER TABLE feedback ADD COLUMN attachment_filename TEXT")
        conn.commit()

    conn.close()

# Initialize DB on load
init_db()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin authentication required to access this page.", "warning")
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    departments = [
        "General Outpatient (OPD) / सामान्य बाह्य रोगी विभाग",
        "Emergency & Casualty / आपातकालीन एवं दुर्घटना चिकित्सा",
        "Pediatrics & Child Care / बाल चिकित्सा एवं शिशु रोग",
        "Maternity & Gynecology / प्रसूति एवं स्त्री रोग",
        "General Medicine / सामान्य चिकित्सा",
        "General Surgery / शल्य चिकित्सा (सर्जरी)",
        "Orthopedics / अस्थि रोग विभाग",
        "Radiology & X-Ray / रेडियोलॉजी एवं एक्स-रे",
        "Pathology / Blood Laboratory / पैथोलॉजी एवं रक्त जांच",
        "Pharmacy & Medicine Counter / औषधालय एवं दवा वितरण",
        "Inpatient / Ward Care / इनडोर वार्ड भर्ती"
    ]
    return render_template("index.html", departments=departments)

@app.route("/submit", methods=["POST"])
def submit_feedback():
    try:
        hospital_name = request.form.get("hospital_name", "").strip() or "District Government General Hospital"
        department = request.form.get("department", "").strip()
        visit_date = request.form.get("visit_date", "").strip() or datetime.now().strftime("%Y-%m-%d")
        patient_type = request.form.get("patient_type", "Self")
        is_emergency = 1 if request.form.get("is_emergency") == "yes" else 0
        
        # Ratings (1 to 5)
        cleanliness_rating = int(request.form.get("cleanliness_rating", 3))
        doctor_rating = int(request.form.get("doctor_rating", 3))
        staff_courtesy_rating = int(request.form.get("staff_courtesy_rating", 3))
        wait_time_rating = int(request.form.get("wait_time_rating", 3))
        overall_rating = int(request.form.get("overall_rating", 3))
        
        # Medicine & Diagnostics
        medicines_available = request.form.get("medicines_available", "Fully Provided")
        diagnostics_available = request.form.get("diagnostics_available", "Fully Available")
        wait_time_duration = request.form.get("wait_time_duration", "30-60 minutes")
        bribe_or_illegal_demand = request.form.get("bribe_or_illegal_demand", "No, everything was transparent")
        
        comments = request.form.get("comments", "").strip()
        citizen_name = request.form.get("citizen_name", "").strip() or "Anonymous Citizen"
        contact_number = request.form.get("contact_number", "").strip()
        
        # Handle File Upload
        attachment_filename = None
        if "attachment" in request.files:
            file = request.files["attachment"]
            if file and file.filename and allowed_file(file.filename):
                safe_name = secure_filename(file.filename)
                unique_prefix = uuid.uuid4().hex[:8]
                attachment_filename = f"{unique_prefix}_{safe_name}"
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], attachment_filename))

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO feedback (
                timestamp, hospital_name, department, visit_date, patient_type,
                is_emergency, cleanliness_rating, doctor_rating, staff_courtesy_rating,
                wait_time_rating, overall_rating, medicines_available, diagnostics_available,
                wait_time_duration, bribe_or_illegal_demand, comments, citizen_name, contact_number,
                attachment_filename
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            timestamp, hospital_name, department, visit_date, patient_type,
            is_emergency, cleanliness_rating, doctor_rating, staff_courtesy_rating,
            wait_time_rating, overall_rating, medicines_available, diagnostics_available,
            wait_time_duration, bribe_or_illegal_demand, comments, citizen_name, contact_number,
            attachment_filename
        ))
        conn.commit()
        submission_id = cursor.lastrowid
        conn.close()

        return redirect(url_for("thank_you", ref_id=f"GH-{submission_id:05d}"))
    except Exception as e:
        flash(f"Error submitting feedback: {str(e)}", "danger")
        return redirect(url_for("index"))

@app.route("/thank-you")
def thank_you():
    ref_id = request.args.get("ref_id", "GH-00001")
    return render_template("thank_you.html", ref_id=ref_id)

@app.route("/poster")
def poster():
    """Printable A4 QR Code Poster for hospital notice boards & OPD waiting halls."""
    return render_template("poster.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("is_admin"):
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["is_admin"] = True
            session["admin_user"] = username
            flash("Welcome back, Administrator. You are now logged in.", "success")
            next_url = request.args.get("next") or url_for("dashboard")
            return redirect(next_url)
        else:
            flash("Invalid administrator credentials. Please check and try again.", "danger")

    return render_template("login.html", default_user=ADMIN_USER)

@app.route("/logout")
def logout():
    session.pop("is_admin", None)
    session.pop("admin_user", None)
    flash("You have been securely logged out.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@admin_required
def dashboard():
    dept_filter = request.args.get("dept", "")
    conn = get_db_connection()
    cursor = conn.cursor()

    base_query = "SELECT * FROM feedback"
    params = []
    if dept_filter:
        base_query += " WHERE department = ?"
        params.append(dept_filter)
    base_query += " ORDER BY id DESC"

    cursor.execute(base_query, params)
    feedbacks = cursor.fetchall()

    # Aggregate metrics
    cursor.execute("SELECT COUNT(*) as count FROM feedback")
    total_count = cursor.fetchone()["count"]

    metrics = {
        "total": total_count,
        "avg_overall": 0.0,
        "avg_cleanliness": 0.0,
        "avg_doctor": 0.0,
        "avg_staff": 0.0,
        "medicine_full_pct": 0,
        "diagnostics_full_pct": 0,
        "attachments_count": 0
    }

    if total_count > 0:
        cursor.execute("""
            SELECT 
                AVG(overall_rating) as avg_overall,
                AVG(cleanliness_rating) as avg_cleanliness,
                AVG(doctor_rating) as avg_doctor,
                AVG(staff_courtesy_rating) as avg_staff,
                AVG(wait_time_rating) as avg_wait
            FROM feedback
        """)
        row = cursor.fetchone()
        metrics["avg_overall"] = round(row["avg_overall"] or 0, 1)
        metrics["avg_cleanliness"] = round(row["avg_cleanliness"] or 0, 1)
        metrics["avg_doctor"] = round(row["avg_doctor"] or 0, 1)
        metrics["avg_staff"] = round(row["avg_staff"] or 0, 1)

        cursor.execute("SELECT COUNT(*) as count FROM feedback WHERE medicines_available LIKE '%All prescribed%' OR medicines_available LIKE '%Fully%'")
        med_count = cursor.fetchone()["count"]
        metrics["medicine_full_pct"] = round((med_count / total_count) * 100)

        cursor.execute("SELECT COUNT(*) as count FROM feedback WHERE diagnostics_available LIKE '%All free%' OR diagnostics_available LIKE '%Fully%'")
        diag_count = cursor.fetchone()["count"]
        metrics["diagnostics_full_pct"] = round((diag_count / total_count) * 100)

        cursor.execute("SELECT COUNT(*) as count FROM feedback WHERE attachment_filename IS NOT NULL AND attachment_filename != ''")
        metrics["attachments_count"] = cursor.fetchone()["count"]

    # Department breakdown for charts
    cursor.execute("""
        SELECT department, COUNT(*) as count, AVG(overall_rating) as avg_score
        FROM feedback
        GROUP BY department
        ORDER BY count DESC
    """)
    dept_stats = cursor.fetchall()

    # Medicine availability breakdown
    cursor.execute("""
        SELECT medicines_available, COUNT(*) as count
        FROM feedback
        GROUP BY medicines_available
    """)
    medicine_stats = cursor.fetchall()

    # Unique departments
    cursor.execute("SELECT DISTINCT department FROM feedback WHERE department != '' ORDER BY department ASC")
    all_depts = [row["department"] for row in cursor.fetchall()]

    conn.close()

    return render_template(
        "dashboard.html",
        feedbacks=feedbacks,
        metrics=metrics,
        dept_stats=dept_stats,
        medicine_stats=medicine_stats,
        all_depts=all_depts,
        selected_dept=dept_filter
    )

@app.route("/uploads/<filename>")
@admin_required
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/export/csv")
@admin_required
def export_csv():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [
        "Feedback ID", "Timestamp", "Hospital Name", "Department", "Visit Date",
        "Patient Type", "Emergency Visit", "Cleanliness (1-5)", "Doctor Consultation (1-5)",
        "Staff Courtesy (1-5)", "Wait Time Rating (1-5)", "Overall Rating (1-5)",
        "Medicines Availability", "Diagnostics Availability", "Wait Time Duration",
        "Integrity/Transparency", "Comments", "Citizen Name", "Contact Number", "Attachment File"
    ]
    writer.writerow(headers)

    for r in rows:
        writer.writerow([
            f"GH-{r['id']:05d}",
            r["timestamp"],
            r["hospital_name"],
            r["department"],
            r["visit_date"],
            r["patient_type"],
            "Yes" if r["is_emergency"] == 1 else "No",
            r["cleanliness_rating"],
            r["doctor_rating"],
            r["staff_courtesy_rating"],
            r["wait_time_rating"],
            r["overall_rating"],
            r["medicines_available"],
            r["diagnostics_available"],
            r["wait_time_duration"],
            r["bribe_or_illegal_demand"],
            r["comments"],
            r["citizen_name"],
            r["contact_number"],
            r["attachment_filename"] or ""
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=hospital_feedback_report_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@app.route("/api/seed", methods=["POST", "GET"])
def seed_sample_data():
    """Seeds realistic sample feedback so the dashboard is immediately demonstrable."""
    samples = [
        ("District Government General Hospital", "General Outpatient (OPD) / सामान्य बाह्य रोगी विभाग", "2026-10-10", "Self", 0, 4, 5, 4, 3, 4, "Fully Provided", "Fully Available", "45 minutes", "No, everything was transparent", "The doctor took time to listen attentively. Waiting queue was slightly long but organized token system helped.", "Ramesh Sharma", "9876543210"),
        ("District Government General Hospital", "Emergency & Casualty / आपातकालीन एवं दुर्घटना चिकित्सा", "2026-10-11", "Family Member", 1, 4, 4, 5, 4, 4, "Fully Provided", "Fully Available", "10 minutes", "No, everything was transparent", "Immediate response from casualty nursing staff when my uncle suffered breathing issues. Oxygen was set up quickly.", "Pooja V.", ""),
        ("District Government General Hospital", "Pharmacy & Medicine Counter / औषधालय एवं दवा वितरण", "2026-10-09", "Self", 0, 3, 4, 3, 2, 3, "Partially Provided", "Not required", "1 hour", "No, everything was transparent", "Antibiotic was available, but paracetamol syrup for child had to be purchased from private chemist.", "Sunil K.", ""),
        ("District Government General Hospital", "Pathology / Blood Laboratory / पैथोलॉजी एवं रक्त जांच", "2026-10-08", "Self", 0, 4, 4, 4, 3, 4, "Fully Provided", "Fully Available", "30 minutes", "No, everything was transparent", "Blood test results were handed over on the same day without any charge. Very helpful.", "Lakshmi Devi", ""),
        ("District Government General Hospital", "Maternity & Gynecology / प्रसूति एवं स्त्री रोग", "2026-10-07", "Family Member", 0, 5, 5, 5, 4, 5, "Fully Provided", "Fully Available", "20 minutes", "No, everything was transparent", "Excellent prenatal checkup facilities and respectful nurses. Very happy with the government hospital care.", "Anjali Patel", "9812345678"),
        ("District Government General Hospital", "Orthopedics / अस्थि रोग विभाग", "2026-10-06", "Self", 0, 3, 3, 2, 2, 2, "Partially Provided", "Had to get done outside", "2 hours", "No, everything was transparent", "X-ray machine had a long queue and technician arrived late. Doctors were skilled though.", "Vijay Kumar", ""),
        ("District Government General Hospital", "Pediatrics & Child Care / बाल चिकित्सा एवं शिशु रोग", "2026-10-11", "Guardian / Attendant", 0, 5, 5, 4, 4, 5, "Fully Provided", "Fully Available", "25 minutes", "No, everything was transparent", "Immunization was handled smoothly. Doctor explained next vaccine schedule nicely.", "Deepak Mehta", "")
    ]

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as count FROM feedback")
    if cursor.fetchone()["count"] == 0:
        for s in samples:
            cursor.execute("""
                INSERT INTO feedback (
                    timestamp, hospital_name, department, visit_date, patient_type,
                    is_emergency, cleanliness_rating, doctor_rating, staff_courtesy_rating,
                    wait_time_rating, overall_rating, medicines_available, diagnostics_available,
                    wait_time_duration, bribe_or_illegal_demand, comments, citizen_name, contact_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), *s))
        conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    init_db()
    print("GovHospital Pulse running on http://127.0.0.1:5000")
    print(f"Admin login credentials -> Username: {ADMIN_USER} | Password: {ADMIN_PASS}")
    app.run(debug=True, port=5000)
