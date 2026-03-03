# smart_finance_app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import joblib
from datetime import datetime
from sqlalchemy import create_engine, text

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Smart Finance AI",
    layout="wide",
    page_icon="💰"
)

# ---------------- DATABASE CONNECTION ----------------
DATABASE_URL = st.secrets["DATABASE_URL"]
engine = create_engine(DATABASE_URL)

# ---------------- CREATE TABLE IF NOT EXISTS ----------------
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS user_history (
            id SERIAL PRIMARY KEY,
            email TEXT,
            company TEXT,
            role TEXT,
            risk_score INT,
            credit_risk TEXT,
            stability_score FLOAT,
            created_at TIMESTAMP
        )
    """))

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
        "company": "Finance Corp"
    },
    "analyst@finance.com": {
        "password": "analyst123",
        "role": "Analyst",
        "company": "Finance Corp"
    },
}

if st.session_state.user is None:
    st.title("🔐 Smart Finance Intelligence – Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if email in users_db and users_db[email]["password"] == password:
            st.session_state.user = users_db[email]
            st.session_state.email = email
            st.rerun()
        else:
            st.error("Invalid Credentials")
    st.stop()

user = st.session_state.user
email = st.session_state.email

# ---------------- SIDEBAR INPUT ----------------
st.sidebar.header("💵 Financial Inputs")

income = st.sidebar.number_input("Income", 10000, 500000, 50000)
emi = st.sidebar.number_input("EMI", 0, 100000, 5000)
investments = st.sidebar.number_input("Investments", 0, 100000, 10000)
credit_used = st.sidebar.number_input("Credit Used", 0, 100000, 20000)
credit_limit = st.sidebar.number_input("Credit Limit", 20000, 200000, 50000)

input_df = pd.DataFrame({
    'Debt_to_Income':[emi/income if income else 0],
    'Expense_Volatility':[0.2],
    'Credit_Utilization':[credit_used/credit_limit if credit_limit else 0],
    'Savings_Ratio':[(income-emi)/income if income else 0],
    'Investments':[investments]
})

# ---------------- PREDICTIONS ----------------
credit_risk = rf_cr.predict(input_df)[0]
financial_stability = rf_fs.predict(input_df)[0]

risk_score = int(300 + financial_stability * 600)
if credit_risk == 1:
    risk_score -= 50
risk_score = max(300, min(900, risk_score))

# ---------------- SAVE TO CLOUD DATABASE ----------------
with engine.begin() as conn:
    conn.execute(text("""
        INSERT INTO user_history 
        (email, company, role, risk_score, credit_risk, stability_score, created_at)
        VALUES (:email, :company, :role, :risk, :credit, :stability, :created)
    """), {
        "email": email,
        "company": user["company"],
        "role": user["role"],
        "risk": risk_score,
        "credit": "High Risk" if credit_risk else "Low Risk",
        "stability": float(financial_stability),
        "created": datetime.now()
    })

# ---------------- DISPLAY ----------------
st.title("📊 AI Risk Intelligence")

col1, col2 = st.columns(2)

with col1:
    st.metric("🏦 Risk Score (300-900)", risk_score)

with col2:
    st.metric("📈 Stability Score", round(financial_stability, 2))

st.write("Credit Risk:", "High Risk" if credit_risk else "Low Risk")

# ---------------- USER HISTORY ----------------
st.subheader("📜 Your History")

history = pd.read_sql(
    text("""
        SELECT risk_score, credit_risk, stability_score, created_at 
        FROM user_history 
        WHERE email=:email 
        ORDER BY id DESC
    """),
    engine,
    params={"email": email}
)

st.dataframe(history, width="stretch")

# ---------------- ADMIN DASHBOARD ----------------
if user["role"] == "Admin":
    st.subheader("🛠 Admin Dashboard")

    admin_df = pd.read_sql(
        "SELECT email, risk_score, credit_risk, created_at FROM user_history",
        engine
    )

    st.dataframe(admin_df, width="stretch")

    st.subheader("📊 Risk Score Distribution")
    fig = px.histogram(admin_df, x="risk_score", nbins=20)
    st.plotly_chart(fig, width="stretch")
