# smart_finance_app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import joblib
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import io
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
    "admin@finance.com":{"password":"admin123","role":"Admin","company":"Finance Corp","lead":"Mr. Aniket Bains"},
    "analyst@finance.com":{"password":"analyst123","role":"Analyst","company":"Finance Corp","lead":"Mr. Aniket Bains"}
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

st.sidebar.header("⚡ Real-Time Scenario Slider")
income_slider = st.sidebar.slider("Adjust Income (%)", 50, 150, 100)
expense_slider = st.sidebar.slider("Adjust Total Expenses (%)", 50, 150, 100)
emi_slider = st.sidebar.slider("Adjust EMI (%)", 50, 150, 100)

# ---------------- CALCULATIONS ----------------
total_expense = (food+travel+mobile+other+emi) * expense_slider/100
savings = income*income_slider/100 - total_expense
adjusted_emi = emi*emi_slider/100

input_df = pd.DataFrame({'Debt_to_Income':[adjusted_emi/(income*income_slider/100) if income else 0],
                         'Expense_Volatility':[np.std([food,travel,mobile,other])],
                         'Credit_Utilization':[credit_used/credit_limit if credit_limit else 0],
                         'Savings_Ratio':[savings/(income*income_slider/100) if income else 0],
                         'Investments':[investments]})

credit_risk = rf_cr.predict(input_df)[0]
financial_stability = rf_fs.predict(input_df)[0]
risk_score = int(300 + (financial_stability*600))
if credit_risk==1: risk_score-=50
risk_score = max(300,min(900,risk_score))
savings_ratio = savings/(income*income_slider/100) if income else 0
credit_util = credit_used/credit_limit if credit_limit else 0

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

# ---------------- RISK GAUGE ----------------
st.subheader("🎯 Risk Gauge")
gauge_color = "green" if risk_score>=750 else "yellow" if risk_score>=600 else "red"
fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=risk_score,
                                   gauge={"axis":{"range":[300,900]},"bar":{"color":gauge_color}}))
st.plotly_chart(fig_gauge, width="stretch")

# ---------------- EXECUTIVE SUMMARY ----------------
st.subheader("🧠 Executive Financial Summary")
summary = "Strong liquidity, excellent discipline." if risk_score>=750 else \
          "Moderate stability, improve savings." if risk_score>=600 else \
          "High risk, reduce debt & expenses."
st.markdown(f"### {summary}")

# ---------------- AI RECOMMENDATIONS ----------------
st.subheader("🤖 AI Recommendations")
if risk_score>=750:
    st.markdown("- ✅ Maintain investments & discipline.\n- ✅ Keep optimized credit usage.")
elif risk_score>=600:
    st.markdown("- ⚡ Increase savings by 10%.\n- ⚡ Reduce credit utilization.")
else:
    st.markdown("- ❌ Cut expenses.\n- ❌ Reduce EMI dependency.\n- ⚠️ Build emergency fund.")

# ---------------- PORTFOLIO SIMULATION ----------------
st.subheader("💼 Portfolio Simulation & ROI")
portfolio = {"Stocks":stock_invest,"Mutual Funds":mf_invest,"Crypto":crypto_invest,"Savings Fund":savings_fund}
portfolio_df = pd.DataFrame(list(portfolio.items()),columns=["Investment Type","Amount"])
portfolio_df["Projected ROI %"] = [0.12,0.08,0.25,0.05]
portfolio_df["Projected Value"] = portfolio_df["Amount"]*(1+portfolio_df["Projected ROI %"])
st.dataframe(portfolio_df)

fig_port = px.bar(portfolio_df,x="Investment Type",y="Projected Value",title="Projected Portfolio Value")
st.plotly_chart(fig_port,width="stretch")

# ---------------- PORTFOLIO HEATMAP ----------------
st.subheader("📊 Portfolio Allocation Heatmap")
fig_heat = px.treemap(portfolio_df, path=["Investment Type"], values="Amount", color="Projected ROI %",
                      color_continuous_scale="Viridis", title="Portfolio ROI Heatmap")
st.plotly_chart(fig_heat,width="stretch")

# ---------------- 12 MONTH PROJECTION ----------------
st.subheader("📈 12 Month Financial Projection")
month_selected = st.slider("Select Month",1,12,6)
projection = np.clip(financial_stability + np.arange(1,13)*0.02,0,1)
fig_proj = px.line(x=np.arange(1,13),y=projection,labels={"x":"Month","y":"Projected Stability"},title="Projected Financial Stability")
fig_proj.add_vline(x=month_selected,line_dash="dash",line_color="red")
st.plotly_chart(fig_proj,width="stretch")

# ---------------- PDF REPORT ----------------
st.subheader("📄 Download Executive PDF Report")
def generate_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = [Paragraph("Ultimate AI Financial Report", styles["Title"]), Spacer(1,20)]
    data=[["Metric","Value"],["Risk Score", str(risk_score)],["Credit Risk","High Risk" if credit_risk else "Low Risk"],
          ["Stability %", f"{financial_stability*100:.2f}%"],["Savings %", f"{savings_ratio*100:.2f}%"]]
    table = Table(data,colWidths=[3*inch,2*inch])
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.darkblue),
                               ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
                               ("GRID",(0,0),(-1,-1),1,colors.black)]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

if st.button("Generate Executive Report"):
    pdf_buffer = generate_pdf()
    st.download_button("Download PDF", pdf_buffer,"Ultimate_Finance_Report.pdf","application/pdf")
