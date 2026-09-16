from flask import Flask, render_template, request, redirect, url_for, session
from functools import wraps
import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
# =====================================================
# SESSION CONFIGURATION
# =====================================================

app.secret_key = os.getenv("SECRET_KEY")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# =====================================================
# DATABASE CONNECTION
# =====================================================

def get_db_connection():

    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306))
    )

    return connection


# =====================================================
# HOME PAGE
# =====================================================

@app.route("/")
def home():
    return render_template("index.html")


# =====================================================
# DATABASE TEST
# =====================================================

@app.route("/test-db")
def test_db():

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        cursor.execute("SELECT DATABASE();")

        database_name = cursor.fetchone()[0]

        cursor.close()
        connection.close()

        return f"""
        <h1>Database Connected Successfully! ✅</h1>
        <p>Connected Database: <strong>{database_name}</strong></p>
        """

    except Exception as e:

        return f"""
        <h1>Database Connection Failed ❌</h1>
        <p>{e}</p>
        """

# =====================================================
# SERVICE ENQUIRY
# =====================================================

@app.route("/submit-enquiry", methods=["POST"])
def submit_enquiry():

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    vehicle = request.form.get("vehicle", "").strip()
    service = request.form.get("service", "").strip()
    message = request.form.get("message", "").strip()

    # Basic validation
    if not name or not phone or not vehicle or not service:
        return "Please fill all required fields.", 400

    # Phone validation
    if not phone.isdigit() or len(phone) != 10:
        return "Please enter a valid 10-digit phone number.", 400

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor()

        query = """
            INSERT INTO enquiries
            (name, phone, vehicle, service, message)
            VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            name,
            phone,
            vehicle,
            service,
            message
        )

        cursor.execute(query, values)

        connection.commit()

        return redirect(url_for("enquiry_success"))

    except Exception as e:

        print("Database Error:", e)

        return "Something went wrong while submitting your enquiry.", 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =====================================================
# ENQUIRY SUCCESS
# =====================================================

@app.route("/enquiry-success")
def enquiry_success():

    return """
    <!DOCTYPE html>

    <html lang="en">

    <head>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <title>Enquiry Submitted | Gupta Tyre House</title>

        <style>

            * {
                box-sizing: border-box;
            }

            body {

                margin: 0;

                min-height: 100vh;

                display: flex;

                align-items: center;

                justify-content: center;

                background: #111;

                font-family: Arial, sans-serif;

                color: white;

            }

            .success-card {

                width: min(90%, 500px);

                padding: 45px;

                background: #ffffff;

                color: #111;

                border-radius: 16px;

                text-align: center;

            }

            .success-icon {

                width: 70px;

                height: 70px;

                margin: 0 auto 20px;

                display: flex;

                align-items: center;

                justify-content: center;

                border-radius: 50%;

                background: #168c45;

                color: white;

                font-size: 32px;

            }

            h1 {

                margin: 0;

                font-size: 30px;

            }

            p {

                color: #666;

                line-height: 1.6;

            }

            a {

                display: inline-block;

                margin-top: 20px;

                padding: 13px 22px;

                background: #d71920;

                color: white;

                text-decoration: none;

                border-radius: 7px;

                font-weight: bold;

            }

        </style>

    </head>

    <body>

        <div class="success-card">

            <div class="success-icon">
                ✓
            </div>

            <h1>
                Enquiry Submitted!
            </h1>

            <p>
                Thank you for contacting Gupta Tyre House.
                Our team will get in touch with you shortly.
            </p>

            <a href="/">
                Back to Website
            </a>

        </div>

    </body>

    </html>
    """


# =====================================================
# ADMIN LOGIN PROTECTION
# =====================================================

def admin_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))

        return function(*args, **kwargs)

    return decorated_function


# =====================================================
# ADMIN LOGIN
# =====================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))

    error = None

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")

        if username == admin_username and password == admin_password:

            session["admin_logged_in"] = True

            return redirect(url_for("admin_dashboard"))

        error = "Invalid username or password."

    return render_template(
        "admin_login.html",
        error=error
    )



# =====================================================
# ADMIN DASHBOARD
# =====================================================

@app.route("/admin")
@admin_required
def admin_dashboard():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(dictionary=True)

        # Get all enquiries
        cursor.execute("""
            SELECT *
            FROM enquiries
            ORDER BY created_at DESC
        """)

        enquiries = cursor.fetchall()

        # Total enquiries
        cursor.execute("""
            SELECT COUNT(*)
            FROM enquiries
        """)

        total = cursor.fetchone()["COUNT(*)"]

        # New enquiries
        cursor.execute("""
            SELECT COUNT(*)
            FROM enquiries
            WHERE status = 'New'
        """)

        new_count = cursor.fetchone()["COUNT(*)"]

        # Completed enquiries
        cursor.execute("""
            SELECT COUNT(*)
            FROM enquiries
            WHERE status = 'Completed'
        """)

        completed = cursor.fetchone()["COUNT(*)"]

        return render_template(
            "admin.html",
            enquiries=enquiries,
            total=total,
            new_count=new_count,
            completed=completed
        )

    except Exception as e:

        print("Admin Dashboard Error:", e)

        return "Unable to load admin dashboard.", 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# =====================================================
# ADMIN LOGOUT
# =====================================================

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect(url_for("admin_login"))



# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=False
    )