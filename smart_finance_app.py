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
import base64

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Ultimate Smart Finance Pro", layout="wide", page_icon="💰")

# ---------------- THEME TOGGLE ----------------
theme = st.sidebar.radio("🌗 Theme", ["Dark","Light"])

# ---------------- FINTECH BACKGROUND IMAGE ----------------
def set_background_image(image_file):
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            background-repeat: no-repeat;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

if theme=="Dark":
    set_background_image("fintech_dark.png")
    card_bg = "#1e2a38"
    section_bg = "#16222a"
    text_color = "white"
else:
    set_background_image("fintech_light.png")
    card_bg = "#ffffff"
    section_bg = "#f0f0f0"
    text_color = "black"

# Apply card & section styles
st.markdown(f"""
<style>
.card {{background-color: {card_bg}; padding: 20px; border-radius: 15px; text-align: center; color:{text_color};}}
.section {{background-color: {section_bg}; padding: 25px; border-radius: 20px; margin-bottom: 25px; color:{text_color};}}
</style>
""", unsafe_allow_html=True)

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

# ---------------- RISK GAUGE ----------------
st.subheader("🎯 Risk Gauge")
gauge_color = "green" if risk_score>=750 else "yellow" if risk_score>=600 else "red"
fig_gauge = go.Figure(go.Indicator(mode="gauge+number", value=risk_score,
                                   gauge={"axis":{"range":[300,900]},"bar":{"color":gauge_color}}))
st.plotly_chart(fig_gauge, width="stretch")

# ---------------- EXECUTIVE SUMMARY ----------------
st.subheader("🧠 Executive Summary")
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
with st.form("report_form"):
    report_name = st.text_input("Your Name", value=user.get("lead",""))
    report_email = st.text_input("Email", value="")
    report_company = st.text_input("Company Name", value=user.get("company",""))
    submit_report = st.form_submit_button("Generate & Download Report")

if submit_report:
    st.balloons()

    def generate_pdf(user_name, email, company_name, risk_score, credit_risk,
                     financial_stability, savings_ratio, input_df,
                     portfolio_df):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=(8.5*inch,11*inch))
        styles = getSampleStyleSheet()
        elements = []

        # Logo
        try:
            logo_path = "logo.png"
            logo = Image(logo_path, width=2*inch, height=2*inch)
            elements.append(logo)
        except: pass
        elements.append(Spacer(1,15))

        # Title
        elements.append(Paragraph("📊 Ultimate AI Financial Report", styles["Title"]))
        elements.append(Spacer(1,15))

        # User Info Table
        user_info = [["👤 Name", user_name],
                     ["📧 Email", email],
                     ["🏢 Company", company_name]]
        table_user = Table(user_info, colWidths=[2.5*inch,5*inch])
        table_user.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.lightblue),
                                        ("TEXTCOLOR",(0,0),(-1,-1),colors.black),
                                        ("GRID",(0,0),(-1,-1),1,colors.black)]))
        elements.append(table_user)
        elements.append(Spacer(1,20))

        # KPI Metrics Table
        kpi_data = [["Metric","Value"],
                    ["🏦 Risk Score", str(risk_score)],
                    ["💳 Credit Risk","High Risk" if credit_risk else "Low Risk"],
                    ["📈 Stability %", f"{financial_stability*100:.2f}%"],
                    ["💰 Savings %", f"{savings_ratio*100:.2f}%"]]
        kpi_table = Table(kpi_data, colWidths=[3*inch,3*inch])
        kpi_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.darkblue),
                                       ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
                                       ("GRID",(0,0),(-1,-1),1,colors.black)]))
        elements.append(kpi_table)
        elements.append(Spacer(1,20))

        # Financial Categories Table
        financial_data = [["Category","Amount (₹)"]]
        for col in input_df.columns:
            financial_data.append([col,f"{input_df[col].values[0]:,.2f}"])
        financial_table = Table(financial_data, colWidths=[4*inch,3*inch])
        financial_table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#4CAF50")),
                                             ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
                                             ("GRID",(0,0),(-1,-1),1,colors.black)]))
        elements.append(financial_table)
        elements.append(Spacer(1,20))

        # Charts
        try:
            # Financial Feature
            fig, ax = plt.subplots(figsize=(5,3))
            input_df.plot(kind="bar", ax=ax, legend=False, color='skyblue')
            ax.set_title("Financial Feature Overview")
            ax.set_ylabel("Value")
            plt.tight_layout()
            chart_path = "temp_feature_chart.png"
            fig.savefig(chart_path)
            plt.close(fig)
            elements.append(Image(chart_path, width=5*inch, height=3*inch))
            elements.append(Spacer(1,15))
        except: pass

        try:
            # Portfolio Bar Chart
            fig, ax = plt.subplots(figsize=(5,3))
            portfolio_df.plot(kind="bar", x="Investment Type", y="Projected Value", ax=ax, color='orange', legend=False)
            ax.set_title("Projected Portfolio Value")
            ax.set_ylabel("Amount (₹)")
            plt.tight_layout()
            port_chart_path = "temp_portfolio_chart.png"
            fig.savefig(port_chart_path)
            plt.close(fig)
            elements.append(Image(port_chart_path, width=5*inch, height=3*inch))
            elements.append(Spacer(1,15))
        except: pass

        try:
            # Portfolio ROI Heatmap
            fig = px.treemap(portfolio_df, path=["Investment Type"], values="Amount", color="Projected ROI %",
                             color_continuous_scale="Viridis", title="Portfolio ROI Heatmap")
            heat_path = "temp_portfolio_heatmap.png"
            fig.write_image(heat_path)
            elements.append(Image(heat_path, width=5*inch, height=3*inch))
            elements.append(Spacer(1,15))
        except: pass

        doc.build(elements)
        buffer.seek(0)
        return buffer

    pdf_buffer = generate_pdf(report_name, report_email, report_company,
                              risk_score, credit_risk, financial_stability,
                              savings_ratio, input_df, portfolio_df)

    st.download_button("Download PDF", pdf_buffer,"Ultimate_Finance_Report.pdf","application/pdf")
