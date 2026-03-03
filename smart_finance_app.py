# smart_finance_app.py

import streamlit as st
import pandas as pd
import numpy as np
import shap
import plotly.express as px
import joblib
import pyodbc
from datetime import datetime

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Smart Finance Intelligence Pro",
    layout="wide",
    page_icon="💰"
)

# ---------------- SQL SERVER CONNECTION ----------------
SERVER = r"LAPTOP-IJ4V7L7Q\SQLEXPRESS"
DATABASE = "SmartFinanceDB"

def create_database():
    conn = pyodbc.connect(
        f"DRIVER={{SQL Server}};"
        f"SERVER={SERVER};"
        f"DATABASE=master;"
        f"Trusted_Connection=yes;"
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(f"IF DB_ID('{DATABASE}') IS NULL CREATE DATABASE {DATABASE}")
    conn.close()

def get_connection():
    return pyodbc.connect(
        f"DRIVER={{SQL Server}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"Trusted_Connection=yes;"
    )

def create_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        IF OBJECT_ID('user_history', 'U') IS NULL
        CREATE TABLE user_history (
            id INT IDENTITY(1,1) PRIMARY KEY,
            email NVARCHAR(100),
            company NVARCHAR(100),
            role NVARCHAR(50),
            risk_score INT,
            credit_risk NVARCHAR(50),
            stability_score FLOAT,
            timestamp NVARCHAR(50)
        )
    """)
    conn.commit()
    conn.close()

create_database()
create_table()

# ---------------- LOAD MODELS ----------------
@st.cache_resource
def load_models():
    return joblib.load("credit_model.pkl"), joblib.load("stability_model.pkl")

rf_cr, rf_fs = load_models()

# ---------------- LOGIN ----------------
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
            st.session_state.email = email
            st.rerun()
        else:
            st.error("Invalid Credentials")

    st.stop()

user = st.session_state.user
email = st.session_state.email

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("## 👤 User Info")
st.sidebar.write(f"**Company:** {user['company']}")
st.sidebar.write(f"**Role:** {user['role']}")

if st.sidebar.button("Logout"):
    st.session_state.user = None
    st.rerun()

# ---------------- INPUTS ----------------
st.sidebar.header("💵 Financial Inputs")

income = st.sidebar.number_input("Income (₹)", 10000, 500000, 50000)
emi = st.sidebar.number_input("EMI Paid (₹)", 0, 100000, 5000)
investments = st.sidebar.number_input("Investments (₹)", 0, 100000, 10000)
credit_used = st.sidebar.number_input("Credit Used (₹)", 0, 100000, 20000)
credit_limit = st.sidebar.number_input("Credit Limit (₹)", 20000, 200000, 50000)

stability_ratio = (income - emi) / income if income else 0
credit_util = credit_used / credit_limit if credit_limit else 0

input_df = pd.DataFrame({
    'Debt_to_Income':[emi/income if income else 0],
    'Expense_Volatility':[0.2],
    'Credit_Utilization':[credit_util],
    'Savings_Ratio':[stability_ratio],
    'Investments':[investments]
})

# ---------------- PREDICTIONS ----------------
credit_risk = rf_cr.predict(input_df)[0]
financial_stability = rf_fs.predict(input_df)[0]

risk_score = int(300 + (financial_stability * 600))
if credit_risk == 1:
    risk_score -= 50
risk_score = max(300, min(900, risk_score))

# ---------------- SAVE TO SQL SERVER ----------------
conn = get_connection()
cursor = conn.cursor()
cursor.execute("""
    INSERT INTO user_history
    (email, company, role, risk_score, credit_risk, stability_score, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (
    email,
    user['company'],
    user['role'],
    risk_score,
    "High Risk" if credit_risk else "Low Risk",
    float(financial_stability),
    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
))
conn.commit()
conn.close()

# ---------------- DISPLAY ----------------
st.title("📊 AI Risk Intelligence")

st.metric("🏦 AI Risk Score (300–900)", risk_score)
st.write("Credit Risk:", "High Risk" if credit_risk else "Low Risk")
st.write("Financial Stability Score:", round(financial_stability,2))

# ---------------- USER HISTORY ----------------
st.subheader("📜 Your Risk History")

conn = get_connection()
history_df = pd.read_sql("SELECT risk_score, credit_risk, stability_score, timestamp FROM user_history WHERE email = ?", conn, params=[email])
conn.close()

st.dataframe(history_df, width='stretch')

# ---------------- ADMIN DASHBOARD ----------------
if user['role'] == "Admin":
    st.subheader("🛠 Admin Dashboard – All Users")

    conn = get_connection()
    admin_df = pd.read_sql("SELECT email, risk_score, credit_risk, timestamp FROM user_history", conn)
    conn.close()

    st.dataframe(admin_df, width='stretch')
