import json
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import os # Added for dummy API key

# Import your custom hybrid retrieval function
from ingest_retrieve import retrieve_top_5 

# ---------------------------------------------------------
# 1. Define the Strict Output Schema for the Dashboard
# ---------------------------------------------------------
class IncidentResolution(BaseModel):
    timestamp: str = Field(description="Timestamp of the first occurrence of the error in the logs.")
    summary: str = Field(description="A concise summary of the incident.")
    root_cause: str = Field(description="Detailed explanation of the underlying cause based on the runbooks. Should be detailes")
    remediation_steps: list = Field(description="List of short steps implemented to resolve the issue")

# ---------------------------------------------------------
# 2. Initialize the LLMs (UPDATED FOR LOCAL SERVER)
# ---------------------------------------------------------
# When using LM Studio or a local server, you must provide a dummy API key.
# The base_url points to your local server's v1 endpoint.

LOCAL_MODEL_URL = "http://127.0.0.1:1234/v1"
DUMMY_API_KEY = "lm-studio" # Or any non-empty string

# Use the local model for the fast summary task
llm_fast = ChatOpenAI(
    base_url=LOCAL_MODEL_URL,
    api_key=DUMMY_API_KEY,
    model="local-model", # The exact string often doesn't matter for local servers, but required by Langchain
    temperature=0
)

# Use the local model for the structured JSON task
# Note: Ensure your local model is strong enough to reliably output JSON!
llm_smart = ChatOpenAI(
    base_url=LOCAL_MODEL_URL,
    api_key=DUMMY_API_KEY,
    model="local-model",
    temperature=0
).with_structured_output(IncidentResolution)

# ---------------------------------------------------------
# 3. Define the Prompts
# ---------------------------------------------------------
summary_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an expert DevOps AI. Analyze the following logs from App, DB, and Infra services. 
    If multiple errors are there in a single service or in multiple service logs create a consolidated version of all the error.
     The summary should not be more than 100 words. Only address the error logs to create the summary."""),
    ("user", "{raw_logs}")
])

resolution_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are an L3 Site Reliability Engineer. Analyze the incident and provide a structured resolution.
    Use the provided historical runbooks to identify the root cause and the remediation steps. Remediation steps should be short and should not be detailed. 
    Remediation steps should be a list of strings. Remediation steps should not be code or SQL query. It should be descriptive explaining the steps to be taken.
    Do not hallucinate commands not found in the runbooks."""),
    ("user", """
    ### Raw Server Logs ###
    {raw_logs}
    
    ### Identified Summary ###
    {summary}
    
    ### Retrieved Knowledge Base (Runbooks & Past Incidents) ###
    {context}
    """)
])

# ---------------------------------------------------------
# 4. The Execution Pipeline (The "Chain")
# ---------------------------------------------------------
def process_incident(app_logs, db_logs, infra_logs):
    print("🚨 Triggering Autonomous Diagnosis Pipeline (Local Model)...")
    
    # Combine logs into a single readable block
    raw_logs = f"APP LOGS:\n{app_logs}\n\nDB LOGS:\n{db_logs}\n\nINFRA LOGS:\n{infra_logs}"
    
    # Step 1: Generate Summary for Search
    print("-> Summarizing logs for semantic search...")
    summary_chain = summary_prompt | llm_fast
    summary_result = summary_chain.invoke({"raw_logs": raw_logs})
    incident_summary = summary_result.content
    
    # Step 2: Hybrid Retrieval 
    print(f"-> Searching Vector DB for: '{incident_summary}'")
    # Utilizing the hybrid search script provided
    retrieved_docs = retrieve_top_5(incident_summary) 
    
    # Format the retrieved documents into a clean string context
    formatted_context = ""
    for doc in retrieved_docs:
        # Extracting the original JSON metadata for context
        formatted_context += f"- {json.dumps(doc['data'])}\n" 
        
    # Step 3: Generate Structured Resolution
    print("-> Generating structured resolution and remediation plan...")
    resolution_chain = resolution_prompt | llm_smart
    final_resolution = resolution_chain.invoke({
        "raw_logs": raw_logs,
        "summary": incident_summary,
        "context": formatted_context
    })
    
    print("✅ Pipeline Complete.")
    return final_resolution

if __name__ == "__main__":
    app_logs = """[2026-06-16 22:21:38] INFO: JWT validated successfully for user session
                    [2026-06-16 22:21:43] INFO: Redis cache hit for room inventory status
                    [2026-06-16 22:21:48] INFO: JWT validated successfully for user session
                    [2026-06-16 22:21:53] INFO: Incoming request to /api/v1/checkout
                    [2026-06-16 22:21:58] INFO: Incoming request to /api/v1/checkout
                    [2026-06-16 22:22:03] INFO: Redis cache hit for room inventory status
                    [2026-06-16 22:22:08] INFO: Incoming request to /api/v1/checkout
                    [2026-06-16 22:22:13] INFO: Redis cache hit for room inventory status
                    [2026-06-16 22:22:18] INFO: JWT validated successfully for user session
                    [2026-06-16 22:24:18] ERROR: java.net.SocketTimeoutException: Read timed out to api.stripe.com
                    """
    
    db_logs = """[2026-06-16 22:21:33] LOG: statement: SELECT * FROM rooms WHERE status='AVAILABLE'
                [2026-06-16 22:21:38] LOG: duration: 12.4ms
                [2026-06-16 22:21:43] LOG: statement: SELECT * FROM rooms WHERE status='AVAILABLE'
                [2026-06-16 22:21:48] LOG: duration: 12.4ms
                [2026-06-16 22:21:53] LOG: duration: 12.4ms
                [2026-06-16 22:21:58] LOG: duration: 12.4ms
                [2026-06-16 22:22:03] LOG: duration: 12.4ms
                [2026-06-16 22:22:08] LOG: duration: 12.4ms
                [2026-06-16 22:22:13] LOG: statement: SELECT * FROM rooms WHERE status='AVAILABLE'
                [2026-06-16 22:22:18] LOG: statement: SELECT * FROM rooms WHERE status='AVAILABLE'"""
    
    infra_logs = """[2026-06-16 22:21:33] INFO: Pod reservation-service-worker memory active: 400Mi
                    [2026-06-16 22:21:38] INFO: Pod reservation-service-worker memory active: 400Mi
                    [2026-06-16 22:21:43] INFO: Pod reservation-service-worker memory active: 400Mi
                    [2026-06-16 22:21:48] INFO: Node-04 CPU utilization steady at 45%
                    [2026-06-16 22:21:53] INFO: S3 document upload successful 200 OK
                    [2026-06-17 00:57:49] INFO: [kubelet] node-02 memory usage 95%
                    [2026-06-17 00:57:51] WARN: Memory cgroup out of memory: Killed process 8812 (java) total-vm:4092100kB, anon-rss:1048576kB
                    [2026-06-17 00:57:55] CRITICAL: Container reservation-service OOMKilled Detected (Exit Code 137)
                    [2026-06-17 00:57:57] ERROR: java.lang.OutOfMemoryError: Java heap space limits reached.
                    [2026-06-17 00:57:58] WARN: Kubernetes Pod reservation-service transitioned to CrashLoopBackOff state."""
    
    print(process_incident(app_logs,db_logs,infra_logs))