# smart_finance_dashboard_full.py
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import numpy as np
import shap
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
import plotly.express as px
import plotly.graph_objects as go
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, Image
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import tempfile

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Smart Finance Intelligence Pro", layout="wide", page_icon="💰")

# ---------------- LOGIN SYSTEM ----------------
if "user" not in st.session_state:
    st.session_state.user = None

users_db = {
    "admin@finance.com": {"password": "admin123", "role": "Admin", "company": "Finance Corp", "lead": "Mr. Aniket Bains"},
    "analyst@finance.com": {"password": "analyst123", "role": "Analyst", "company": "Finance Corp", "lead": "Mr. Aniket Bains"},
}

if st.session_state.user is None:
    st.title("🔐 Smart Finance Intelligence – Secure Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if email in users_db and users_db[email]["password"] == password:
            st.session_state.user = users_db[email]
            st.stop()
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
    st.experimental_rerun()

st.markdown("""
<style>
.stApp {background-color:#0E1117;color:#E6EDF3;}
.kpi-card {background: linear-gradient(145deg,#1E222B,#161B22);padding:20px;border-radius:15px;border:1px solid #2D333B;text-align:center;margin-bottom:10px;}
.kpi-title {color:#9CA3AF;font-size:14px;}
.kpi-value {color:#FFFFFF;font-size:26px;font-weight:bold;}
footer {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------- HEADER ----------------
st.markdown(f"""
<div style='padding:10px 0px'>
<h1>💰 {user['company']} – Smart Finance Dashboard Pro</h1>
<p style='color:#9CA3AF;'>Finance AI Powered Intelligence • Secure Multi-User SaaS</p>
</div>
""", unsafe_allow_html=True)

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
        'Income':[income],
        'Food_Expense':[food],
        'Travel_Expense':[travel],
        'Mobile_Expense':[mobile],
        'Other_Expenses':[other],
        'EMI':[emi],
        'Investments':[investments],
        'Debt_to_Income':[debt_to_income],
        'Expense_Volatility':[expense_volatility],
        'Credit_Utilization':[credit_utilization],
        'Savings_Ratio':[savings_ratio]
    })

input_df = user_input_features()
st.subheader("📄 User Input Data")
st.dataframe(input_df)

# ---------------- DUMMY MODELS ----------------
rf_cr = RandomForestClassifier(n_estimators=15, random_state=42)
X_dummy = np.random.rand(200,5)
y_dummy_cr = np.random.randint(0,2,200)
rf_cr.fit(X_dummy, y_dummy_cr)

rf_fs = RandomForestRegressor(n_estimators=15, random_state=42)
y_dummy_fs = np.random.rand(200)
rf_fs.fit(X_dummy, y_dummy_fs)

X_input = input_df[['Debt_to_Income','Expense_Volatility','Credit_Utilization','Savings_Ratio','Investments']]

# ---------------- PREDICTIONS ----------------
credit_risk = rf_cr.predict(X_input)[0]
financial_stability = rf_fs.predict(X_input)[0]

st.subheader("📊 Predicted Scores")
st.markdown(f"- **Credit Risk:** {'High' if credit_risk==1 else 'Low'}")
st.markdown(f"- **Financial Stability Score (0-1):** {financial_stability:.2f}")

# ---------------- KPI CARDS ----------------
st.subheader("📈 KPIs Overview")
col1, col2, col3 = st.columns(3)
def kpi(title,value):
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>{title}</div><div class='kpi-value'>{value}</div></div>", unsafe_allow_html=True)

with col1: kpi("Debt-to-Income", f"{input_df['Debt_to_Income'][0]:.2f}")
with col2: kpi("Credit Utilization", f"{input_df['Credit_Utilization'][0]*100:.1f}%")
with col3: kpi("Savings Ratio", f"{input_df['Savings_Ratio'][0]*100:.1f}%")

# ---------------- SHAP ANALYSIS ----------------
explainer_cr = shap.TreeExplainer(rf_cr)
shap_values_cr = explainer_cr.shap_values(X_input)
shap_vals_cr_plot = np.array(shap_values_cr[1]) if isinstance(shap_values_cr, list) else np.array(shap_values_cr)
if shap_vals_cr_plot.ndim==1: shap_vals_cr_plot = shap_vals_cr_plot.reshape(1,-1)
shap_abs_mean_cr = np.abs(shap_vals_cr_plot).mean(axis=0)
shap_abs_mean_cr = np.array(shap_abs_mean_cr).flatten()
feature_names = [str(f) for f in X_input.columns]
min_len = min(len(feature_names), len(shap_abs_mean_cr))
feature_names = feature_names[:min_len]
shap_abs_mean_cr = shap_abs_mean_cr[:min_len]
shap_abs_mean_cr = [float(x) for x in shap_abs_mean_cr]
shap_df_cr = pd.DataFrame({'Feature': feature_names,'Importance': shap_abs_mean_cr}).sort_values(by='Importance', ascending=True)

# ---------------- SHAP BAR CHART ----------------
fig_shap = px.bar(shap_df_cr, x='Importance', y='Feature', orientation='h', color='Importance', color_continuous_scale='Viridis', title="Credit Risk Feature Importance")
st.plotly_chart(fig_shap)

# ---------------- EXPENSE BREAKDOWN ----------------
st.subheader("📊 Expense Breakdown")
expense_df = input_df[['Food_Expense','Travel_Expense','Mobile_Expense','Other_Expenses']]
fig_expense = px.pie(expense_df, values=expense_df.iloc[0], names=expense_df.columns, title="Expense Distribution")
st.plotly_chart(fig_expense)

# ---------------- FINANCIAL RADAR ----------------
st.subheader("📈 Financial Health Radar")
radar_df = pd.DataFrame({
    'Metrics':['Debt-to-Income','Credit Utilization','Savings Ratio','Expense Volatility','Investments'],
    'Value':[input_df['Debt_to_Income'][0], input_df['Credit_Utilization'][0], input_df['Savings_Ratio'][0],
             input_df['Expense_Volatility'][0]/1000, input_df['Investments'][0]/50000]
})
fig_radar = go.Figure()
fig_radar.add_trace(go.Scatterpolar(r=radar_df['Value'], theta=radar_df['Metrics'], fill='toself', name='User Metrics'))
fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0,1])), showlegend=False, title="Financial Health Radar")
st.plotly_chart(fig_radar)

# ---------------- RECOMMENDATIONS ----------------
st.subheader("💡 Recommendations")
if credit_risk==1: st.markdown("- Reduce EMI / debt burden\n- Keep credit utilization <30%")
else: st.markdown("- Credit looks healthy! Maintain good habits.")
if financial_stability < 0.5: st.markdown("- Save more and control expenses")
else: st.markdown("- Financial stability is good")

# ---------------- PDF REPORT ----------------
st.subheader("📄 Download PDF Report")
def generate_pdf():
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    doc = SimpleDocTemplate(tmp_file.name)
    styles = getSampleStyleSheet()
    elements = []
    elements.append(Paragraph(f"{user['company']} – Smart Finance Intelligence Report", styles['Title']))
    elements.append(Paragraph(f"Finance Lead: {user['lead']}", styles['Normal']))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1,12))
    
    # User Data Table
    elements.append(Paragraph("User Input Data:", styles['Heading2']))
    data_table = [[col,input_df[col][0]] for col in input_df.columns]
    t = Table(data_table)
    elements.append(t)
    elements.append(Spacer(1,12))
    
    # Predictions
    elements.append(Paragraph("Predictions:", styles['Heading2']))
    elements.append(Paragraph(f"Credit Risk: {'High' if credit_risk==1 else 'Low'}", styles['Normal']))
    elements.append(Paragraph(f"Financial Stability Score: {financial_stability:.2f}", styles['Normal']))
    
    doc.build(elements)
    return tmp_file.name

if st.button("Generate & Download PDF"):
    pdf_file = generate_pdf()
    with open(pdf_file,"rb") as f:
        st.download_button("Download Report", f, file_name="Finance_Report_Pro.pdf", mime="application/pdf")
