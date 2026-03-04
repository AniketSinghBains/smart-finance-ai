# smart_finance_app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import io
import matplotlib.pyplot as plt
import time

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Ultimate Smart Finance Pro", layout="wide", page_icon="💰")

# ---------------- THEME TOGGLE ----------------
theme = st.sidebar.radio("🌗 Theme", ["Dark","Light"])
if theme=="Dark":
    st.markdown("""
    <style>
    .stApp {background: linear-gradient(to right, #0f2027, #203a43, #2c5364); color: white;}
    .card {background-color: #1e2a38; padding: 20px; border-radius: 15px; text-align: center;}
    .section {background-color: #16222a; padding: 25px; border-radius: 20px; margin-bottom: 25px;}
    </style>""", unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
    .stApp {background: linear-gradient(to right, #f5f7fa, #c3cfe2, #e2e2e2); color: black;}
    .card {background-color: #ffffff; padding: 20px; border-radius: 15px; text-align: center; color:black;}
    .section {background-color: #f0f0f0; padding: 25px; border-radius: 20px; margin-bottom: 25px; color:black;}
    </style>""", unsafe_allow_html=True)

# ---------------- LOAD MODELS ----------------
@st.cache_resource
def load_models():
    return joblib.load("credit_model.pkl"), joblib.load("stability_model.pkl")
rf_cr, rf_fs = load_models()

# ---------------- LOGIN ----------------
if "user" not in st.session_state: st.session_state.user = None
users_db = {
    "admin@finance.com":{"password":"admin123","role":"Admin","company":"Finance Corp","lead":"Aniket Bains"},
    "analyst@finance.com":{"password":"analyst123","role":"Analyst","company":"Finance Corp","lead":"Aniket Bains"}
}

if st.session_state.user is None:
    st.title("🔐 Ultimate Smart Finance – Secure Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email in users_db and users_db[email]["password"]==password:
            st.session_state.user = users_db[email]; st.rerun()
        else: st.error("Invalid Credentials")
    st.stop()
user = st.session_state.user

# ---------------- SIDEBAR ----------------
st.sidebar.markdown("## 👤 User Info")
st.sidebar.write(f"**Company:** {user['company']}")
st.sidebar.write(f"**Role:** {user['role']}")
st.sidebar.write(f"**Finance Lead:** {user['lead']}")
if st.sidebar.button("Logout"): st.session_state.user=None; st.rerun()

# ---------------- FINANCIAL INPUTS ----------------
st.sidebar.header("💵 Financial Inputs")
income = st.sidebar.number_input("Income (₹)", 10000,500000,50000)
food = st.sidebar.number_input("Food Expense (₹)",1000,50000,5000)
travel = st.sidebar.number_input("Travel Expense (₹)",500,10000,2000)
mobile = st.sidebar.number_input("Mobile Expense (₹)",300,5000,500)
other = st.sidebar.number_input("Other Expenses (₹)",1000,50000,5000)
emi = st.sidebar.number_input("EMI Paid (₹)",0,100000,2000)
investments = st.sidebar.number_input("Investments (₹)",0,100000,10000)
credit_used = st.sidebar.number_input("Credit Used (₹)",0,100000,20000)
credit_limit = st.sidebar.number_input("Credit Limit (₹)",20000,200000,50000)

st.sidebar.header("📊 Portfolio Simulation")
stock_invest = st.sidebar.number_input("Stocks (₹)",0,200000,10000)
mf_invest = st.sidebar.number_input("Mutual Funds (₹)",0,200000,10000)
crypto_invest = st.sidebar.number_input("Crypto (₹)",0,100000,5000)
savings_fund = st.sidebar.number_input("Savings Fund (₹)",0,200000,10000)

st.sidebar.header("⚡ Scenario Adjustment")
income_slider = st.sidebar.slider("Adjust Income (%)", 50, 150, 100)
expense_slider = st.sidebar.slider("Adjust Total Expenses (%)", 50, 150, 100)
emi_slider = st.sidebar.slider("Adjust EMI (%)", 50, 150, 100)

# ---------------- CALCULATION FUNCTION ----------------
def calculate_metrics():
    total_expense = (food+travel+mobile+other+emi)*expense_slider/100
    savings = income*income_slider/100 - total_expense
    adjusted_emi = emi*emi_slider/100
    input_df = pd.DataFrame({
        'Debt_to_Income':[adjusted_emi/(income*income_slider/100) if income else 0],
        'Expense_Volatility':[np.std([food,travel,mobile,other])],
        'Credit_Utilization':[credit_used/credit_limit if credit_limit else 0],
        'Savings_Ratio':[savings/(income*income_slider/100) if income else 0],
        'Investments':[investments]
    })
    credit_risk = rf_cr.predict(input_df)[0]
    financial_stability = rf_fs.predict(input_df)[0]
    risk_score = int(300 + financial_stability*600)
    if credit_risk==1: risk_score-=50
    risk_score = max(300,min(900,risk_score))
    savings_ratio = savings/(income*income_slider/100) if income else 0
    credit_util = credit_used/credit_limit if credit_limit else 0
    return risk_score, credit_risk, financial_stability, savings_ratio, credit_util, savings, input_df

risk_score, credit_risk, financial_stability, savings_ratio, credit_util, savings, input_df = calculate_metrics()

# ---------------- KPI DASHBOARD ----------------
st.title("📊 Ultimate AI Finance Dashboard")
col1,col2,col3,col4 = st.columns(4)
def animated_metric(col,label,value):
    placeholder = col.empty()
    for i in range(0,value+1,int(max(1,value/50))):
        placeholder.metric(label,i)
        time.sleep(0.01)

animated_metric(col1,"🏦 Risk Score",risk_score)
animated_metric(col2,"📈 Stability %",int(financial_stability*100))
animated_metric(col3,"💰 Savings %",int(savings_ratio*100))
animated_metric(col4,"💳 Credit Util %",int(credit_util*100))
st.divider()

# ---------------- REPORT FORM INPUT ----------------
st.subheader("📄 Enter Info for Report")
with st.form("report_form"):
    report_company = st.text_input("Company Name", value=user.get("company",""))
    report_lead = st.text_input("Finance Lead", value=user.get("lead",""))
    report_email = st.text_input("Email", value="")
    submit_report = st.form_submit_button("Generate & Download Report")
    
    if submit_report:
        st.balloons()  # Balloon animation
        def generate_pdf(user_name, company_name, email, risk_score, credit_risk, financial_stability, savings_ratio, input_df):
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=(8.5*inch,11*inch))
            styles = getSampleStyleSheet()
            elements = []
            elements.append(Paragraph("📊 Ultimate AI Financial Report", styles["Title"]))
            elements.append(Spacer(1,15))
            user_info = [["User Name", user_name],
                         ["Email", email],
                         ["Company", company_name]]
            table_user = Table(user_info,colWidths=[3*inch,4*inch])
            table_user.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightblue),
                                            ("GRID",(0,0),(-1,-1),1,colors.black)]))
            elements.append(table_user)
            elements.append(Spacer(1,15))
            kpi_data = [["Metric","Value"],
                        ["Risk Score", str(risk_score)],
                        ["Credit Risk","High Risk" if credit_risk else "Low Risk"],
                        ["Stability %", f"{financial_stability*100:.2f}%"],
                        ["Savings %", f"{savings_ratio*100:.2f}%"]]
            kpi_table = Table(kpi_data,colWidths=[3*inch,2*inch])
            kpi_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.darkblue),
                                           ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
                                           ("GRID",(0,0),(-1,-1),1,colors.black)]))
            elements.append(kpi_table)
            elements.append(Spacer(1,15))
            financial_data = [["Category","Amount (₹)"]]
            for col in input_df.columns:
                financial_data.append([col,f"{input_df[col].values[0]:,.2f}"])
            financial_table = Table(financial_data,colWidths=[4*inch,3*inch])
            financial_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.green),
                                                 ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
                                                 ("GRID",(0,0),(-1,-1),1,colors.black)]))
            elements.append(financial_table)
            doc.build(elements)
            buffer.seek(0)
            return buffer
        
        pdf_buffer = generate_pdf(user_name=report_lead, company_name=report_company, email=report_email,
                                  risk_score=risk_score, credit_risk=credit_risk, financial_stability=financial_stability,
                                  savings_ratio=savings_ratio, input_df=input_df)
        st.download_button("Download PDF", pdf_buffer,"Ultimate_Finance_Report.pdf","application/pdf")
