import logging
from datetime import datetime
from backend.database import db_connection

logger = logging.getLogger("audit_service")

def log_action(user_id: int, action: str, ip_address: str, status: str, details: str = None):
    """
    Saves an audit record to the audit_logs table.
    Gracefully logs locally if database insert fails.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Redact sensitive parameters from details for privacy protection
    sanitized_details = details
    if details and ("password" in details.lower() or "token" in details.lower()):
        sanitized_details = "[REDACTED FOR SECURITY]"
        
    try:
        db_connection.execute_query(
            """
            INSERT INTO audit_logs (user_id, action, ip_address, timestamp, status, details) 
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, action, ip_address, timestamp, status, sanitized_details)
        )
        logger.info(f"Audit Logged: {action} | User: {user_id} | Status: {status} | IP: {ip_address}")
    except Exception as e:
        logger.error(f"Audit Logging to database failed: {e}. Falling back to logger: \
                    Action={action}, User={user_id}, Status={status}, Details={sanitized_details}")
