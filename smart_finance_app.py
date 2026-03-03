# smart_finance_dashboard_full.py

import streamlit as st
import pandas as pd
import numpy as np
import shap
import plotly.express as px
import joblib
import os
import tempfile
from datetime import datetime

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

st.set_page_config(page_title="Smart Finance Intelligence Pro",
                   layout="wide",
                   page_icon="💰")

# ---------------- LOAD MODELS ----------------
@st.cache_resource
def load_models():
    return joblib.load("credit_model.pkl"), joblib.load("stability_model.pkl")

rf_cr, rf_fs = load_models()

# ---------------- LOGIN ----------------
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

# ---------------- INPUTS ----------------
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

# ---------------- DISPLAY ----------------
st.title("📊 AI Risk Intelligence")

st.metric("🏦 AI Risk Score (300–900)", risk_score)
st.write("Credit Risk:", "High Risk" if credit_risk else "Low Risk")
st.write("Financial Stability Score:", round(financial_stability,2))

# ---------------- AI INSIGHT ----------------
st.subheader("🤖 AI Financial Insight")

if risk_score >= 750:
    st.success("Excellent profile. You are eligible for premium financial products.")
elif risk_score >= 650:
    st.info("Good stability. Optimize savings for better score.")
elif risk_score >= 550:
    st.warning("Moderate risk. Reduce EMI and credit usage.")
else:
    st.error("High financial risk. Immediate correction required.")

# ---------------- SHAP ----------------
st.subheader("📊 Model Explainability")

try:
    explainer = shap.TreeExplainer(rf_cr)
    shap_values = explainer.shap_values(input_df)

    # Handle multi-output or binary classification safely
    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    shap_values = np.array(shap_values)

    # Flatten properly
    shap_values = shap_values.reshape(-1)

    importance = np.abs(shap_values)

    shap_df = pd.DataFrame({
        "Feature": input_df.columns,
        "Impact": importance
    })

    fig = px.bar(
        shap_df,
        x="Impact",
        y="Feature",
        orientation="h",
        title="Feature Impact on Risk Score"
    )

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.warning("SHAP visualization temporarily unavailable.")
# ---------------- 12 MONTH PROJECTION ----------------
st.subheader("📈 12 Month Projection")

months = np.arange(1,13)
growth = np.clip(financial_stability + months*0.02, 0, 1)
fig2 = px.line(x=months, y=growth,
               labels={"x":"Month","y":"Projected Stability"})
st.plotly_chart(fig2, use_container_width=True)

# ---------------- PDF ----------------
st.subheader("📄 Download Professional PDF")

def generate_pdf():
    file_path = "Finance_Report_Pro.pdf"
    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("AI Financial Intelligence Report", styles["Title"]))
    elements.append(Spacer(1, 20))

    data = [
        ["Metric","Value"],
        ["Risk Score", str(risk_score)],
        ["Credit Risk","High Risk" if credit_risk else "Low Risk"],
        ["Stability", f"{financial_stability:.2f}"]
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

if st.button("Generate Report"):
    path = generate_pdf()
    with open(path,"rb") as f:
        st.download_button("Download PDF",f,"Finance_Report_Pro.pdf","application/pdf")

