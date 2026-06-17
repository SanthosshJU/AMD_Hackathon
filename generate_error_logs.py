import os
from datetime import datetime, timedelta

# Define the base directory structure
BASE_DIR = "./mock_error_scenarios"
SERVICES = ["app_server", "database", "infrastructure"]

for service in SERVICES:
    os.makedirs(os.path.join(BASE_DIR, service), exist_ok=True)

# Generate realistic timestamps
now = datetime.now()
def get_time(offset_seconds):
    return (now - timedelta(seconds=offset_seconds)).strftime("%Y-%m-%d %H:%M:%S")

# =====================================================================
# 1. APP SERVER ERROR SCENARIOS
# =====================================================================
app_errors = {
    "error_scenario_1.log": f"""[{get_time(10)}] INFO: Outbound request to Stripe API initiated
[{get_time(8)}] WARN: External API latency exceeding 4000ms threshold
[{get_time(4)}] ERROR: java.net.SocketTimeoutException: Read timed out to api.stripe.com
[{get_time(2)}] ERROR: Resilience4j CircuitBreaker payment-gateway-cb CHANGED_STATE FROM CLOSED TO OPEN
[{get_time(1)}] ERROR: Payment conversion failed for transaction tx-9921. HTTP 500 returned to client.""",

    "error_scenario_2.log": f"""[{get_time(10)}] INFO: Validating user token payload for session
[{get_time(8)}] INFO: Fetching JWKS public key from cache
[{get_time(4)}] ERROR: io.jsonwebtoken.SignatureException: The Token Signature is invalid
[{get_time(2)}] WARN: JWT signature does not match locally cached credentials from auth-service
[{get_time(1)}] ERROR: Security context rejected. HTTP 401 Unauthorized returned to client.""",

    "error_scenario_3.log": f"""[{get_time(10)}] INFO: Attempting to lock room PR-101 for checkout reservation
[{get_time(8)}] WARN: Redis transaction contention rate increasing > 40%
[{get_time(4)}] ERROR: com.hotel.exception.RedisLockException: Could not acquire distributed lock for Room Type Resource ID: PR-101
[{get_time(2)}] ERROR: Inventory sync failed. Stale Redisson distributed locks suspected.
[{get_time(1)}] ERROR: Room mapping locked by another transaction. Front-end displaying Unavailable.""",

    "error_scenario_4.log": f"""[{get_time(10)}] INFO: Executing promo_booking workflow for 50 concurrent users
[{get_time(8)}] INFO: Updating customer_ledger table followed by room_inventory table
[{get_time(4)}] ERROR: org.springframework.dao.DeadlockLoserDataAccessException: PreparedStatementCallback; SQL statement []; Deadlock detected
[{get_time(2)}] ERROR: nested exception is org.postgresql.util.PSQLException: ERROR: deadlock detected
[{get_time(1)}] ERROR: Transaction aborted to resolve deadlock. Checkout failed.""",

    "error_scenario_5.log": f"""[{get_time(10)}] INFO: Night audit trigger: Generating PDF invoice for customer 8821
[{get_time(8)}] INFO: Uploading to S3 bucket path: s3://hotel-invoices-prod/2026-06-16/
[{get_time(4)}] ERROR: com.amazonaws.services.s3.model.AmazonS3Exception: Status Code: 503, Error Code: SlowDown, Please reduce your request rate.
[{get_time(2)}] WARN: Invoice Storage Dispatch Drop Rate > 25%
[{get_time(1)}] ERROR: Background worker queue full. PDF generation task dropped."""
}

# =====================================================================
# 2. DATABASE ENGINE ERROR SCENARIOS
# =====================================================================
db_errors = {
    "error_scenario_1.log": f"""[{get_time(10)}] LOG: connection authorized: user=booking_app database=hotel_reservations
[{get_time(8)}] LOG: statement: BEGIN TRANSACTION ISOLATION LEVEL READ COMMITTED
[{get_time(4)}] FATAL: remaining connection slots are reserved for non-replication superuser connections
[{get_time(2)}] ERROR: HikariCP booking-service-pool - Connection is not available, request timed out after 30000ms
[{get_time(1)}] WARN: Connection Count Exceeded 95% of max_connections limit.""",

    "error_scenario_2.log": f"""[{get_time(10)}] LOG: statement: SELECT * FROM bookings WHERE customer_id = 998231 AND status = 'ACTIVE' ORDER BY checkin_date DESC;
[{get_time(8)}] WARN: Database Read Latency Spike > 3000ms detected.
[{get_time(4)}] WARN: pg_log: duration: 4210.512 ms statement: SELECT * FROM bookings WHERE customer_id = 998231 AND status = 'ACTIVE' ORDER BY checkin_date DESC;
[{get_time(2)}] LOG: execution plan: Seq Scan on bookings (cost=0.00..15432.00 rows=1420 width=128)
[{get_time(1)}] WARN: Missing relational DB index causing full sequential table scans.""",

    "error_scenario_3.log": f"""[{get_time(10)}] LOG: statement: UPDATE room_inventory SET status='LOCKED' WHERE room_id=102;
[{get_time(8)}] LOG: statement: UPDATE customer_ledger SET balance=0 WHERE customer_id=55;
[{get_time(4)}] ERROR: deadlock detected
[{get_time(2)}] DETAIL: Process 4102 waits for ShareLock on transaction 881203; blocked by process 4115
[{get_time(1)}] LOG: statement: ABORT. Row-level transaction deadlock resolved by dropping process 4102.""",

    "error_scenario_4.log": f"""[{get_time(10)}] INFO: [node-1] cluster health status changed from [GREEN] to [RED] (reason: [shards failed])
[{get_time(8)}] ERROR: org.elasticsearch.indices.IndexPrimaryShardNotAllocatedException: [hotel_rooms][2] primary shard is unassigned
[{get_time(4)}] WARN: 0 nodes are actively participating in shard [hotel_rooms][2]
[{get_time(2)}] ERROR: ClusterHealthIsRedException: Backend search index mappings are unmapped.
[{get_time(1)}] ERROR: Search API search-api-service queries failing with HTTP 500.""",

    "error_scenario_5.log": f"""[{get_time(10)}] LOG: statement: SELECT * FROM pg_stat_activity WHERE state = 'idle in transaction';
[{get_time(8)}] WARN: 95 active connections stuck in 'idle in transaction' state for over 3 minutes.
[{get_time(4)}] WARN: Unclosed connection objects detected originating from 'billing-orchestrator'
[{get_time(2)}] FATAL: Transaction pool starved. No available slots.
[{get_time(1)}] LOG: executing pg_terminate_backend() to drop rogue PIDs."""
}

# =====================================================================
# 3. INFRASTRUCTURE & METRICS ERROR SCENARIOS
# =====================================================================
infra_errors = {
    "error_scenario_1.log": f"""[{get_time(10)}] INFO: [kubelet] node-02 memory usage 95%
[{get_time(8)}] WARN: Memory cgroup out of memory: Killed process 8812 (java) total-vm:4092100kB, anon-rss:1048576kB
[{get_time(4)}] CRITICAL: Container reservation-service OOMKilled Detected (Exit Code 137)
[{get_time(2)}] ERROR: java.lang.OutOfMemoryError: Java heap space limits reached.
[{get_time(1)}] WARN: Kubernetes Pod reservation-service transitioned to CrashLoopBackOff state.""",

    "error_scenario_2.log": f"""[{get_time(10)}] INFO: fluentd file tailer started on /var/log/hotel-app/booking-engine-trace.log
[{get_time(8)}] WARN: Host Storage Utilization Alert: /var/log exceeding 96% availability limits
[{get_time(4)}] ERROR: IOError: [Errno 28] No space left on device
[{get_time(2)}] CRITICAL: Application daemon output handlers failing to write trace logs.
[{get_time(1)}] WARN: logrotate system services failed to execute due to zero block space.""",

    "error_scenario_3.log": f"""[{get_time(10)}] INFO: [aws-ec2] checking node health for es-data-03
[{get_time(8)}] CRITICAL: kernel panic - not syncing: Fatal exception in interrupt
[{get_time(4)}] WARN: Kubernetes node es-data-03 transitioned to NotReady
[{get_time(2)}] INFO: Evicting pods from node es-data-03 due to hardware failure
[{get_time(1)}] ERROR: Node reboot sequence stalled. Max_retries limit hit.""",

    "error_scenario_4.log": f"""[{get_time(10)}] INFO: [cloudwatch-agent] compiling S3 traffic metrics
[{get_time(8)}] WARN: S3 partition rate throttling thresholds exceeded.
[{get_time(4)}] CRITICAL: 4,000 PUT requests per second detected on prefix s3://hotel-invoices-prod/2026-06-16/
[{get_time(2)}] ERROR: Exceeded AWS limit of 3,500 PUTs per prefix.
[{get_time(1)}] WARN: AWS S3 Quota Throttling activated. Invoice queue backing up.""",

    "error_scenario_5.log": f"""[{get_time(10)}] INFO: [metrics-server] scraping node resources for db-cluster
[{get_time(8)}] WARN: pg-master.internal.hotelapp.net load average spiked to 45.2
[{get_time(4)}] CRITICAL: Database engine host core processor utilization spikes to 100% capacity.
[{get_time(2)}] WARN: High CPU utilization pinned by full sequential table scans.
[{get_time(1)}] ERROR: DB Node CPU threshold exceeded. Queries backing up in process queue."""
}

# Write files to disk
def write_logs(service_name, error_dict):
    for filename, content in error_dict.items():
        filepath = os.path.join(BASE_DIR, service_name, filename)
        with open(filepath, "w") as f:
            f.write(content)

write_logs("app_server", app_errors)
write_logs("database", db_errors)
write_logs("infrastructure", infra_errors)

print(f"✅ Successfully generated 15 mock error log files in '{BASE_DIR}/'!")