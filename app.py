"""
SPF Industrial Specialty Performance Flooring — Flask Application
Serves the landing page and handles form submissions via SMTP.
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import requests
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from dotenv import load_dotenv
#
# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
load_dotenv()

app = Flask(
    __name__,
    static_folder="assets",      # keeps existing HTML asset paths working
    static_url_path="/assets",   # assets/css/styles.css → /assets/css/styles.css
    template_folder="templates",
)

app.config.update(
    # SMTP
    SMTP_HOST=os.getenv("SMTP_HOST", "smtp.gmail.com"),
    SMTP_PORT=int(os.getenv("SMTP_PORT", "465")),
    SMTP_USER=os.getenv("SMTP_USER", ""),
    SMTP_PASS=os.getenv("SMTP_PASS", ""),

    # Recipients
    CONTACT_RECEIVER=os.getenv("CONTACT_RECEIVER", ""),
    CONTACT_CC=os.getenv("CONTACT_CC", ""),  # comma-separated

    # reCAPTCHA v2
    RECAPTCHA_SECRET=os.getenv("RECAPTCHA_SECRET", ""),
    RECAPTCHA_SITE_KEY=os.getenv("RECAPTCHA_SITE_KEY", ""),
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────
def verify_recaptcha(token: str) -> bool:
    """Verify Google reCAPTCHA v2 token server-side."""
    secret = app.config["RECAPTCHA_SECRET"]
    if not secret:
        logger.warning("RECAPTCHA_SECRET not set — skipping verification.")
        return True

    try:
        resp = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={"secret": secret, "response": token},
            timeout=5,
        )
        result = resp.json()
        return result.get("success", False)
    except Exception as exc:
        logger.error("reCAPTCHA verification failed: %s", exc)
        return False


def send_email(name: str, address: str, email: str, phone: str, service: str) -> bool:
    """Send the lead notification email via SMTP SSL."""
    cfg = app.config

    if not cfg["SMTP_USER"] or not cfg["SMTP_PASS"]:
        logger.error("SMTP credentials not configured.")
        return False

    # Build message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"SPF Industrial — New Request from {name}"
    msg["From"] = cfg["SMTP_USER"]
    msg["To"] = cfg["CONTACT_RECEIVER"] or cfg["SMTP_USER"]

    # CC recipients
    cc_list = [
        addr.strip()
        for addr in cfg["CONTACT_CC"].split(",")
        if addr.strip()
    ]
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)

    all_recipients = [msg["To"]] + cc_list

    html_body = f"""\
    <h3>SPF Industrial — New Request Form Submission</h3>
    <p><strong>Full Name:</strong> {name}</p>
    <p><strong>Property Address:</strong> {address}</p>
    <p><strong>Email:</strong> {email}</p>
    <p><strong>Phone:</strong> {phone}</p>
    <p><strong>Service Requested:</strong> {service}</p>
    """
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP_SSL(cfg["SMTP_HOST"], cfg["SMTP_PORT"], timeout=10) as server:
            server.login(cfg["SMTP_USER"], cfg["SMTP_PASS"])
            server.sendmail(cfg["SMTP_USER"], all_recipients, msg.as_string())
        logger.info("Email sent successfully to %s", all_recipients)
        return True
    except Exception as exc:
        logger.error("SMTP send failed: %s", exc)
        return False


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────
@app.route("/")
def index():
    """Serve the main landing page."""
    return render_template("index.html")

@app.route("/epoxy-flooring")
def epoxy_flooring():
    return render_template("epoxy-flooring.html")


@app.route("/metallic-epoxy")
def metallic_epoxy():
    return render_template("metallic-epoxy.html")


@app.route("/quartz-epoxy")
def quartz_epoxy():
    return render_template("quartz-epoxy.html")


@app.route("/urethane-cement")
def urethane_cement():
    return render_template("urethane-cement.html")


@app.route("/grind-seal")
def grind_seal():
    return render_template("grind-seal.html")


@app.route("/polished-concrete")
def polished_concrete():
    return render_template("polished-concrete.html")

@app.route("/thank-you")
def thank_you():
    """Success page after form submission."""
    return render_template("thank-you.html")


@app.route("/form-error")
def form_error():
    """Error page for failed submissions."""
    return render_template("form-error.html")


@app.route("/submit-form", methods=["POST"])
def submit_form():
    """Handle contact form submission."""

    # 1. Verify reCAPTCHA
    recaptcha_token = request.form.get("g-recaptcha-response", "")
    if not verify_recaptcha(recaptcha_token):
        logger.warning("reCAPTCHA verification failed.")
        return redirect(url_for("form_error"))

    # 2. Extract & validate fields
    name = request.form.get("full_name", "").strip()
    address = request.form.get("address", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    service = request.form.get("service", "").strip()

    if not all([name, address, email, phone, service]):
        logger.warning("Missing required form fields.")
        return redirect(url_for("form_error"))

    # 3. Send email
    if send_email(name, address, email, phone, service):
        
        return redirect(url_for("thank_you"))

    return redirect(url_for("form_error"))

# ──────────────────────────────────────────────
# SEO: robots.txt & sitemap.xml
# ──────────────────────────────────────────────
@app.route("/google98d4dae4aa1a1e2e.html")
def google_verification():
    """Google Search Console site verification."""
    return send_from_directory(app.template_folder, "google98d4dae4aa1a1e2e.html", mimetype="text/html")


@app.route("/robots.txt")
def robots():
    """Serve robots.txt from templates directory."""
    return send_from_directory(app.template_folder, "robots.txt", mimetype="text/plain")


@app.route("/sitemap.xml")
def sitemap():
    """Serve sitemap.xml from templates directory."""
    return send_from_directory(app.template_folder, "sitemap.xml", mimetype="application/xml")


# ──────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)