# smart_finance_app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Smart Finance Intelligence Pro",
    layout="wide",
    page_icon="💰"
)

# ---------------- CUSTOM CSS (Premium UI) ----------------
st.markdown("""
<style>
.stApp {
    background: linear-gradient(to right, #0f2027, #203a43, #2c5364);
    color: white;
}
.card {
    background-color: #1e2a38;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
}
.section {
    background-color: #16222a;
    padding: 25px;
    border-radius: 20px;
    margin-bottom: 25px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOAD MODELS ----------------
@st.cache_resource
def load_models():
    return joblib.load("credit_model.pkl"), joblib.load("stability_model.pkl")

rf_cr, rf_fs = load_models()

# ---------------- LOGIN SYSTEM ----------------
if "user" not in st.session_state:
    st.session_state.user = None

users_db = {
    "admin@finance.com": {
        "password": "admin123",
        "role": "Admin",
        "company": "Finance Corp",
        "lead": "Mr. Aniket Bains"
    },
    "analyst@finance.com": {
        "password": "analyst123",
        "role": "Analyst",
        "company": "Finance Corp",
        "lead": "Mr. Aniket Bains"
    },
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

st.sidebar.header("💵 Financial Inputs")

income = st.sidebar.number_input("Income (₹)", 10000, 500000, 50000)
food = st.sidebar.number_input("Food Expense (₹)", 1000, 50000, 5000)
travel = st.sidebar.number_input("Travel Expense (₹)", 500, 10000, 2000)
mobile = st.sidebar.number_input("Mobile Expense (₹)", 300, 5000, 500)
other = st.sidebar.number_input("Other Expenses (₹)", 1000, 50000, 5000)
emi = st.sidebar.number_input("EMI Paid (₹)", 0, 100000, 2000)
investments = st.sidebar.number_input("Investments (₹)", 0, 100000, 10000)
credit_used = st.sidebar.number_input("Credit Used (₹)", 0, 100000, 20000)
credit_limit = st.sidebar.number_input("Credit Limit (₹)", 20000, 200000, 50000)

total_expense = food + travel + mobile + other + emi
savings = income - total_expense

input_df = pd.DataFrame({
    'Debt_to_Income':[emi/income if income else 0],
    'Expense_Volatility':[np.std([food, travel, mobile, other])],
    'Credit_Utilization':[credit_used/credit_limit if credit_limit else 0],
    'Savings_Ratio':[savings/income if income else 0],
    'Investments':[investments]
})

# ---------------- PREDICTIONS ----------------
credit_risk = rf_cr.predict(input_df)[0]
financial_stability = rf_fs.predict(input_df)[0]

risk_score = int(300 + (financial_stability * 600))
if credit_risk == 1:
    risk_score -= 50
risk_score = max(300, min(900, risk_score))

savings_ratio = savings/income if income else 0
credit_util = credit_used/credit_limit if credit_limit else 0

# ---------------- KPI DASHBOARD ----------------
st.title("📊 AI Risk Intelligence Dashboard")

col1, col2, col3, col4 = st.columns(4)

col1.metric("🏦 Risk Score", risk_score)
col2.metric("📈 Stability %", f"{financial_stability*100:.1f}%")
col3.metric("💰 Savings %", f"{savings_ratio*100:.1f}%")
col4.metric("💳 Credit Util %", f"{credit_util*100:.1f}%")

st.divider()

# ---------------- RISK GAUGE ----------------
st.subheader("🎯 Risk Gauge")

if risk_score >= 750:
    gauge_color = "green"
elif risk_score >= 600:
    gauge_color = "yellow"
else:
    gauge_color = "red"

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=risk_score,
    gauge={
        "axis": {"range": [300, 900]},
        "bar": {"color": gauge_color}
    }
))

st.plotly_chart(fig_gauge, width="stretch")

# ---------------- EXECUTIVE SUMMARY ----------------
st.subheader("🧠 Executive Financial Summary")

if risk_score >= 750:
    summary = "User demonstrates strong liquidity position with excellent financial discipline and optimized credit management."
elif risk_score >= 600:
    summary = "User maintains moderate financial stability with scope for improving savings ratio and reducing liabilities."
else:
    summary = "User shows elevated financial risk exposure with high dependency on credit and low savings buffer."

st.markdown(f"### {summary}")

st.divider()

# ---------------- FEATURE IMPORTANCE ----------------
st.subheader("📊 Feature Importance")

importances = rf_cr.feature_importances_

importance_df = pd.DataFrame({
    "Feature": input_df.columns,
    "Impact": importances
}).sort_values(by="Impact", ascending=True)

fig = px.bar(
    importance_df,
    x="Impact",
    y="Feature",
    orientation="h",
    title="Feature Impact on Credit Risk"
)

st.plotly_chart(fig, width="stretch")

# ---------------- 12 MONTH PROJECTION ----------------
st.subheader("📈 12 Month Financial Projection")

months = np.arange(1, 13)
projection = np.clip(financial_stability + months * 0.02, 0, 1)

fig2 = px.line(
    x=months,
    y=projection,
    labels={"x": "Month", "y": "Projected Stability"},
    title="Projected Financial Stability (12 Months)"
)

st.plotly_chart(fig2, width="stretch")

# ---------------- PDF REPORT ----------------
st.subheader("📄 Download Executive PDF Report")

def generate_pdf():
    file_path = "Finance_Report_Pro.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Executive AI Financial Report", styles["Title"]))
    elements.append(Spacer(1, 20))

    data = [
        ["Metric","Value"],
        ["Risk Score", str(risk_score)],
        ["Credit Risk","High Risk" if credit_risk else "Low Risk"],
        ["Stability %", f"{financial_stability*100:.2f}%"],
        ["Savings %", f"{savings_ratio*100:.2f}%"]
    ]

    table = Table(data, colWidths=[3*inch,2*inch])
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.darkblue),
        ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
        ("GRID",(0,0),(-1,-1),1,colors.black)
    ]))

    elements.append(table)
    doc.build(elements)

    return file_path

if st.button("Generate Executive Report"):
    path = generate_pdf()
    with open(path,"rb") as f:
        st.download_button("Download PDF",f,"Finance_Report_Pro.pdf","application/pdf")
