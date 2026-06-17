import streamlit as st
import json
import os
import time
import random
import uuid
import re
from datetime import datetime
import pytz
import html
import warnings

# Suppress the specific transformer path warnings
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

# --- Environmental Assumptions Guard ---
try:
    import backend_app
except ImportError:
    st.error("Critical: `backend_app.py` not found in the current directory. Please ensure it exists.")
    st.stop()

# --- Configuration & Constants ---
ST_DB_FILE = "incidents_database.json"
SERVERS = {
    "Application": "app_server",
    "Database": "database",
    "Infrastructure": "infrastructure"
}

st.set_page_config(page_title="Autonomous Incident Resolution", page_icon="🤖", layout="wide")

# --- State Initialization ---
def init_state():
    if "pointers" not in st.session_state:
        st.session_state.pointers = {val: 0 for val in SERVERS.values()}
    if "statuses" not in st.session_state:
        st.session_state.statuses = {val: "RUNNING" for val in SERVERS.values()}
    if "buffers" not in st.session_state:
        st.session_state.buffers = {val: [] for val in SERVERS.values()}
    if "pending_analysis" not in st.session_state:
        st.session_state.pending_analysis = None

init_state()

# --- Helper Functions ---
def get_current_ist_str() -> str:
    """Returns the current timestamp in IST."""
    ist_tz = pytz.timezone('Asia/Kolkata')
    return datetime.now(ist_tz).strftime("%Y-%m-%d %H:%M:%S IST")

def convert_to_ist(log_line: str) -> str:
    """Removes existing timestamps and prepends the current IST timestamp."""
    # Matches common timestamp formats (e.g., 2023-10-12 12:00:00 or ISO8601 with/without brackets)
    pattern = r"\[?\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?\]?\s*"
    clean_line = re.sub(pattern, "", log_line).strip()
    
    # Strip lingering hyphens or colons left over from formatting
    if clean_line.startswith("- "):
        clean_line = clean_line[2:]
        
    return f"[{get_current_ist_str()}] {clean_line}"

def read_next_lines(server_id: str, num_lines: int = 1) -> list:
    """Reads the next N lines from the given server's mock log."""
    filepath = os.path.join("mock_logs", f"{server_id}.log")
    if not os.path.exists(filepath):
        return [f"[WARNING] {filepath} not found."]
    
    lines_read = []
    try:
        with open(filepath, "r") as f:
            # Fast-forward to current pointer
            for _ in range(st.session_state.pointers[server_id]):
                f.readline()
                
            for _ in range(num_lines):
                line = f.readline()
                if not line:
                    break # EOF reached
                lines_read.append(convert_to_ist(line.strip()))
                st.session_state.pointers[server_id] += 1
    except Exception as e:
        lines_read.append(f"[ERROR] Failed to read {filepath}: {str(e)}")
        
    return lines_read

def load_incidents() -> list:
    """Safely loads incidents from the JSON database."""
    if not os.path.exists(ST_DB_FILE):
        return []
    try:
        with open(ST_DB_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []

def update_incident_status(incident_id: str, new_status: str):
    """Updates the database entry to the newly provided status."""
    data = load_incidents()
    for row in data:
        if row.get("id") == incident_id:
            row["status"] = new_status
    with open(ST_DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def trigger_error_simulation(server_id: str):
    """Phase 1: Appends logs and updates statuses, then triggers UI rerun before analysis."""
    error_dir = os.path.join("mock_error_scenarios", server_id)
    
    err_lines = []
    if os.path.exists(error_dir):
        files = [f for f in os.listdir(error_dir) if f.endswith(".log")]
        if files:
            chosen = random.choice(files)
            try:
                with open(os.path.join(error_dir, chosen), "r") as f:
                    err_lines = f.readlines()
            except Exception as e:
                err_lines = [f"[SIMULATION ERROR] Could not read {chosen}: {str(e)}"]
    else:
        err_lines = [f"[SYSTEM ERROR] Scenario directory {error_dir} missing."]

    # Append to buffer with a hidden marker and Halt
    formatted_errs = [f"!!ERROR!!{convert_to_ist(line.strip())}" for line in err_lines]
    st.session_state.buffers[server_id].extend(formatted_errs)
    st.session_state.statuses[server_id] = "HALTED"
    
    # Flag analysis to occur AFTER the UI has drawn the new logs
    st.session_state.pending_analysis = server_id


# --- UI Construction ---

# 1. Sidebar Control Panel
with st.sidebar:
    st.title("⚙️ Simulation Control Panel")
    st.markdown("---")
    if st.button("🚨 Simulate Application Error", use_container_width=True):
        trigger_error_simulation("app_server")
        st.rerun()
    if st.button("🚨 Simulate Database Error", use_container_width=True):
        trigger_error_simulation("database")
        st.rerun()
    if st.button("🚨 Simulate Infrastructure Error", use_container_width=True):
        trigger_error_simulation("infrastructure")
        st.rerun()

# 2. Main Layout Header
col1, col2 = st.columns([2, 1])
with col1:
    st.title("🤖 Autonomous Incident Resolution")
    st.markdown("Real-time log aggregation and automated response framework.")

analysis_status_container = st.empty()

# 3. Main Layout Tabs
tab1, tab2, tab3 = st.tabs(["📊 System Overview", "📡 Live Logs Stream", "🗄️ Incident Database"])

# --- Tab 1: System Overview ---
with tab1:
    st.subheader("Current Node Statuses")
    c1, c2, c3 = st.columns(3)
    metrics = [c1, c2, c3]
    
    for idx, (name, s_id) in enumerate(SERVERS.items()):
        status = st.session_state.statuses[s_id]
        color = "green" if status == "RUNNING" else "red" if status == "HALTED" else "orange"
        with metrics[idx]:
            st.markdown(f"""
            <div style="padding: 20px; border-radius: 8px; border: 1px solid #444; background-color: #1e1e1e;">
                <h3 style="margin:0; padding:0; text-align:center;">{name}</h3>
                <p style="margin:0; padding-top:10px; text-align:center; font-size: 20px; color:{color}; font-weight: bold;">
                    {status}
                </p>
            </div>
            """, unsafe_allow_html=True)

# --- Tab 2: Live Logs Stream ---
with tab2:
    lc1, lc2, lc3 = st.columns(3)
    log_cols = [lc1, lc2, lc3]
    
    for idx, (name, s_id) in enumerate(SERVERS.items()):
        with log_cols[idx]:
            st.markdown(f"**{name} Logs**")
            display_lines = st.session_state.buffers[s_id][-100:]
            
            # Format and inject RED span for lines marked as error
            safe_lines = []
            for line in display_lines:
                if line.startswith("!!ERROR!!"):
                    clean_line = html.escape(line.replace("!!ERROR!!", ""))
                    safe_lines.append(f'<span style="color: #ff4b4b;">{clean_line}</span>')
                else:
                    safe_lines.append(html.escape(line))
                    
            log_text = "<br>".join(safe_lines) if safe_lines else "<i>Awaiting stream...</i>"
            
            st.markdown(f"""
            <div style="height: 450px; overflow-y: auto; background-color: #0d1117; color: #00ff00; 
                        padding: 12px; font-family: 'Courier New', monospace; font-size: 13px; 
                        border-radius: 6px; border: 1px solid #30363d; display: flex; flex-direction: column-reverse;">
                <div>{log_text}</div>
            </div>
            """, unsafe_allow_html=True)

# --- Tab 3: Incident Database ---
with tab3:
    st.subheader("Identified Incidents & Remediation Tracking")
    db_data = load_incidents()
    
    if not db_data:
        st.write("No incidents recorded yet.")
    else:
        hc1, hc2, hc3, hc4, hc5 = st.columns([1.5, 2.5, 2.5, 3.5, 1.5])
        hc1.markdown("**Timestamp (IST)**")
        hc2.markdown("**Summary**")
        hc3.markdown("**Root Cause**")
        hc4.markdown("**Remediation Steps**")
        hc5.markdown("**Actions**")
        st.markdown("---")
        
        for row in reversed(db_data): 
            rc1, rc2, rc3, rc4, rc5 = st.columns([1.5, 2.5, 2.5, 3.5, 1.5])
            rc1.write(row.get("timestamp", "N/A"))
            rc2.write(row.get("summary", "N/A"))
            rc3.write(row.get("root_cause", "N/A"))
            
            # Format list of dictionaries safely
            raw_steps = row.get("remediation_steps", [])
            if isinstance(raw_steps, list):
                parsed_steps = [s.get('step', str(s)) if isinstance(s, dict) else str(s) for s in raw_steps]
                formatted_steps = "".join([f"• {s}  \n" for s in parsed_steps])
                rc4.markdown(formatted_steps)
            else:
                rc4.write(str(raw_steps))
            
            with rc5:
                if row.get("status") == "Pending":
                    if st.button("Mark as Complete", key=f"mark_{row['id']}"):
                        target = row.get("target_server", "app_server")
                        st.session_state.statuses[target] = "RUNNING"
                        update_incident_status(row["id"], "Completed")
                        st.rerun()
                else:
                    st.markdown("✅ **Completed**")
            st.markdown("---")

# --- Phase 2: Pending Analysis Engine ---
if st.session_state.pending_analysis:
    server_id = st.session_state.pending_analysis
    
    # Pre-emptively tick logs for running servers so they don't freeze during the spinner wait
    for s_id, s_status in st.session_state.statuses.items():
        if s_status == "RUNNING":
            new_lines = read_next_lines(s_id, num_lines=1)
            if new_lines:
                st.session_state.buffers[s_id].extend(new_lines)
    
    with analysis_status_container.status("🚨 **Incident Detected! Processing Workflow...**", expanded=True) as status:
        st.write("🔍 Analyzing the logs...")
        time.sleep(1.5)
        st.write("📄 Extracting source documents...")
        time.sleep(1.5)
        st.write("💡 Formulating solution...")
        
        # Remove the internal !!ERROR!! tag so the backend gets clean text
        app_logs = [l.replace("!!ERROR!!", "") for l in st.session_state.buffers["app_server"][-10:]]
        db_logs = [l.replace("!!ERROR!!", "") for l in st.session_state.buffers["database"][-10:]]
        infra_logs = [l.replace("!!ERROR!!", "") for l in st.session_state.buffers["infrastructure"][-10:]]
        
        try:
            response = backend_app.process_incident(app_logs, db_logs, infra_logs)
        except Exception as e:
            response = {
                "summary": f"Backend evaluation failed: {str(e)}",
                "root_cause": "Unknown due to processing failure",
                "remediation_steps": [{"step": "Check backend configuration"}, {"step": "Re-evaluate logs"}]
            }
            
        status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
        
    if hasattr(response, "model_dump"):
        incident_record = response.model_dump()
    elif hasattr(response, "dict"):
        incident_record = response.dict()
    else:
        incident_record = dict(response)

    incident_record["timestamp"] = get_current_ist_str()
    incident_record["id"] = str(uuid.uuid4())[:8]
    incident_record["status"] = "Pending"
    incident_record["target_server"] = server_id

    db_data = load_incidents()
    db_data.append(incident_record)
    with open(ST_DB_FILE, "w") as f:
        json.dump(db_data, f, indent=4)
        
    st.session_state.pending_analysis = None
    time.sleep(1) 
    st.rerun()


# --- Background Streaming Routine ---
if not st.session_state.pending_analysis and any(status == "RUNNING" for status in st.session_state.statuses.values()):
    time.sleep(3)
    for server_id, status in st.session_state.statuses.items():
        if status == "RUNNING":
            new_lines = read_next_lines(server_id, num_lines=1)
            if new_lines:
                st.session_state.buffers[server_id].extend(new_lines)
    st.rerun()