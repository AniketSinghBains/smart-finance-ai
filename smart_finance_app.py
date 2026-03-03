# smart_finance_dashboard_full.py
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import numpy as np
import shap
import plotly.express as px
import plotly.graph_objects as go
import joblib
import os
import tempfile
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Smart Finance Intelligence Pro",
                   layout="wide",
                   page_icon="💰")

# ---------------- LOAD TRAINED MODELS ----------------
@st.cache_resource
def load_models():
    if not os.path.exists("credit_model.pkl") or not os.path.exists("stability_model.pkl"):
        st.error("Model files not found. Please run train_model.py first.")
        st.stop()
    return joblib.load("credit_model.pkl"), joblib.load("stability_model.pkl")

rf_cr, rf_fs = load_models()

# ---------------- LOGIN SYSTEM ----------------
if "user" not in st.session_state:
    st.session_state.user = None

users_db = {
    "admin@finance.com": {"password": "admin123", "role": "Admin",
                          "company": "Finance Corp", "lead": "Mr. Aniket Bains"},
    "analyst@finance.com": {"password": "analyst123", "role": "Analyst",
                            "company": "Finance Corp", "lead": "Mr. Aniket Bains"},
}

if st.session_state.user is None:
    st.title("🔐 Smart Finance Intelligence – Secure Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email in users_db and users_db[email]["password"] == password:
            st.session_state.user = users_db[email]
            st.rerun()
        else:
            st.error("Invalid Credentials")
    st.stop()

user = st.session_state.user

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("## 👤 User Info")
st.sidebar.write(f"**Company:** {user['company']}")
st.sidebar.write(f"**Role:** {user['role']}")
st.sidebar.write(f"**Finance Lead:** {user['lead']}")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

# ---------------- USER INPUTS ----------------
st.sidebar.header("💵 Financial Inputs")

def user_input_features():
    income = st.sidebar.number_input("Income (₹)", 10000, 500000, 50000)
    food = st.sidebar.number_input("Food Expense (₹)", 1000, 50000, 5000)
    travel = st.sidebar.number_input("Travel Expense (₹)", 500, 10000, 2000)
    mobile = st.sidebar.number_input("Mobile Expense (₹)", 300, 5000, 500)
    other = st.sidebar.number_input("Other Expenses (₹)", 1000, 50000, 5000)
    emi = st.sidebar.number_input("EMI Paid (₹)", 0, 100000, 0)
    investments = st.sidebar.number_input("Investments (₹)", 0, 100000, 10000)
    credit_used = st.sidebar.number_input("Credit Used (₹)", 0, 100000, 20000)
    credit_limit = st.sidebar.number_input("Credit Limit (₹)", 20000, 200000, 50000)

    total_expense = food + travel + mobile + other + emi
    savings = income - total_expense

    savings_ratio = savings / income if income else 0
    debt_to_income = emi / income if income else 0
    expense_volatility = np.std([food, travel, mobile, other])
    credit_utilization = credit_used / credit_limit if credit_limit else 0

    return pd.DataFrame({
        'Debt_to_Income':[debt_to_income],
        'Expense_Volatility':[expense_volatility],
        'Credit_Utilization':[credit_utilization],
        'Savings_Ratio':[savings_ratio],
        'Investments':[investments]
    })

input_df = user_input_features()

st.subheader("📄 Processed Financial Features")
st.dataframe(input_df)

# ---------------- PREDICTIONS ----------------
credit_risk = rf_cr.predict(input_df)[0]
financial_stability = rf_fs.predict(input_df)[0]

# ---------------- BANKING STYLE RISK SCORE ----------------
risk_score = int(300 + (financial_stability * 600))
if credit_risk == 1:
    risk_score -= 50
risk_score = max(300, min(900, risk_score))

# ---------------- DISPLAY SCORES ----------------
st.subheader("📊 AI Risk Intelligence")

st.metric("🏦 AI Risk Score (300–900)", risk_score)
st.write("Credit Risk:", "High Risk" if credit_risk else "Low Risk")
st.write("Financial Stability Score:", round(financial_stability, 2))

# ---------------- PDF REPORT ----------------
st.subheader("📄 Download Professional PDF Report")

def generate_pdf():
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp_file.name)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(
        f"{user['company']} - Financial Intelligence Report",
        styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph(
        f"Finance Lead: {user['lead']}",
        styles["Normal"]))
    elements.append(Paragraph(
        f"Generated On: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
        styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Score Table
    score_data = [
        ["Metric", "Value"],
        ["AI Risk Score (300-900)", str(risk_score)],
        ["Credit Classification", "High Risk" if credit_risk else "Low Risk"],
        ["Financial Stability Score", f"{financial_stability:.2f}"]
    ]

    score_table = Table(score_data, colWidths=[3*inch, 2*inch])
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("ALIGN",(0,0),(-1,-1),"CENTER")
    ]))

    elements.append(score_table)
    elements.append(Spacer(1, 25))

    doc.build(elements)
    return tmp_file.name


if st.button("Generate & Download PDF"):
    pdf_file = generate_pdf()
    with open(pdf_file, "rb") as f:
        st.download_button("Download Report",
                           f,
                           file_name="Finance_Report_Pro.pdf",
                           mime="application/pdf")
