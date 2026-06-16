import streamlit as st
import time
from datetime import datetime, timedelta

st.set_page_config(
 page_title="Log Diagnosis Remediation Dashboard",
 layout="wide"
)

# -----------------------------
# Sample Data
# -----------------------------
records = [
 {
 "S.No": 1,
 "Timestamp": (datetime.now() - timedelta(minutes=12)).strftime("%Y-%m-%d %H:%M:%S"),
 "Issue": "High application response latency detected",
 "Root Cause": "Thread pool saturation observed in application server logs",
 "Resolution": "Increase application worker thread pool size",
 "Remediation Steps": "Update server thread pool config and restart application service"
 },
 {
 "S.No": 2,
 "Timestamp": (datetime.now() - timedelta(minutes=25)).strftime("%Y-%m-%d %H:%M:%S"),
 "Issue": "Database connection timeout errors",
 "Root Cause": "Connection pool exhausted due to long-running SQL queries",
 "Resolution": "Optimize slow queries and increase DB connection pool limit",
 "Remediation Steps": "Kill stale DB sessions, tune SQL indexes, and update pool settings"
 },
 {
 "S.No": 3,
 "Timestamp": (datetime.now() - timedelta(minutes=41)).strftime("%Y-%m-%d %H:%M:%S"),
 "Issue": "Frequent application server restarts",
 "Root Cause": "OutOfMemoryError found in application server logs",
 "Resolution": "Increase JVM heap memory and analyze memory leaks",
 "Remediation Steps": "Update JVM Xmx value, enable heap dump, and restart application"
 },
 {
 "S.No": 4,
 "Timestamp": (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S"),
 "Issue": "CPU utilization above threshold",
 "Root Cause": "Infrastructure metrics show sustained CPU usage above 90%",
 "Resolution": "Scale application instances horizontally",
 "Remediation Steps": "Add additional application server node and rebalance traffic"
 },
 {
 "S.No": 5,
 "Timestamp": (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
 "Issue": "Disk space warning on database server",
 "Root Cause": "Database logs and infra metrics indicate rapid archive log growth",
 "Resolution": "Clean old archive logs and increase disk capacity",
 "Remediation Steps": "Backup archive logs, purge expired logs, and expand storage volume"
 }
]

# -----------------------------
# Custom CSS
# -----------------------------
st.markdown(
 """
 <style>
 .main-title {
 font-size: 32px;
 font-weight: 700;
 color: #1f2937;
 margin-bottom: 5px;
 }

 .subtitle {
 font-size: 16px;
 color: #6b7280;
 margin-bottom: 25px;
 }

 .table-header {
 background: linear-gradient(90deg, #1f2937, #374151);
 color: white;
 font-weight: 700;
 padding: 14px 10px;
 border-radius: 10px;
 text-align: center;
 font-size: 14px;
 }

 .table-cell {
 background-color: #ffffff;
 padding: 14px 10px;
 border-radius: 10px;
 min-height: 95px;
 box-shadow: 0 2px 8px rgba(0,0,0,0.08);
 font-size: 14px;
 color: #111827;
 display: flex;
 align-items: center;
 }

 .sno-cell {
 justify-content: center;
 font-weight: 700;
 color: #2563eb;
 }

 div.stButton > button {
 background-color: #16a34a;
 color: white;
 border: none;
 border-radius: 6px;
 padding: 10px 18px;
 font-weight: 700;
 width: 100%;
 height: 48px;
 }

 div.stButton > button:hover {
 background-color: #15803d;
 color: white;
 border: none;
 }

 div.stButton > button:active {
 background-color: #166534;
 color: white;
 }

 .toast-message {
 position: fixed;
 top: 70px;
 right: 30px;
 z-index: 9999;
 padding: 16px 22px;
 border-radius: 10px;
 color: white;
 font-weight: 700;
 box-shadow: 0 8px 20px rgba(0,0,0,0.25);
 animation: slideIn 0.3s ease-out;
 }

 .toast-loading {
 background-color: #2563eb;
 }

 .toast-success {
 background-color: #16a34a;
 }

 @keyframes slideIn {
 from {
 opacity: 0;
 transform: translateX(30px);
 }
 to {
 opacity: 1;
 transform: translateX(0);
 }
 }
 </style>
 """,
 unsafe_allow_html=True
)

# -----------------------------
# Page Header
# -----------------------------
st.markdown('<div class="main-title">Log Diagnosis Remediation Dashboard</div>', unsafe_allow_html=True)
st.markdown(
 '<div class="subtitle">Issues diagnosed from application server logs, database logs, and infrastructure metrics logs</div>',
 unsafe_allow_html=True
)

toast_placeholder = st.empty()

# -----------------------------
# Function to show remediation status
# -----------------------------
def show_remediation_status():
 toast_placeholder.markdown(
 """
 <div class="toast-message toast-loading">
 Implementing Remediation
 </div>
 """,
 unsafe_allow_html=True
 )

 time.sleep(5)

 toast_placeholder.markdown(
 """
 <div class="toast-message toast-success">
 Remediation Implemented
 </div>
 """,
 unsafe_allow_html=True
 )

 time.sleep(3)
 toast_placeholder.empty()

# -----------------------------
# Table Header
# -----------------------------
header_cols = st.columns([0.6, 1.4, 2.0, 2.2, 2.0, 2.6, 1.6])

headers = [
 "S.No",
 "Timestamp",
 "Issue",
 "Root Cause",
 "Resolution",
 "Remediation Steps",
 "Button"
]

for col, header in zip(header_cols, headers):
 col.markdown(f'<div class="table-header">{header}</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------
# Table Rows
# -----------------------------
for record in records:
 row_cols = st.columns([0.6, 1.4, 2.0, 2.2, 2.0, 2.6, 1.6])

 row_cols[0].markdown(
 f'<div class="table-cell sno-cell">{record["S.No"]}</div>',
 unsafe_allow_html=True
 )

 row_cols[1].markdown(
 f'<div class="table-cell">{record["Timestamp"]}</div>',
 unsafe_allow_html=True
 )

 row_cols[2].markdown(
 f'<div class="table-cell">{record["Issue"]}</div>',
 unsafe_allow_html=True
 )

 row_cols[3].markdown(
 f'<div class="table-cell">{record["Root Cause"]}</div>',
 unsafe_allow_html=True
 )

 row_cols[4].markdown(
 f'<div class="table-cell">{record["Resolution"]}</div>',
 unsafe_allow_html=True
 )

 row_cols[5].markdown(
 f'<div class="table-cell">{record["Remediation Steps"]}</div>',
 unsafe_allow_html=True
 )

 with row_cols[6]:
    st.write("")
    if st.button( "Implement Remediation", key=f"remediate_{record['S.No']}" ):
        show_remediation_status()

 st.markdown("<br>", unsafe_allow_html=True)