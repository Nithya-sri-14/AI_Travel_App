from fastapi import APIRouter, Depends, Query
from backend.database import db_connection
from backend.api import users

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = Query(50, description="Number of logs to fetch"),
    offset: int = Query(0, description="Offset for pagination"),
    current_admin: dict = Depends(users.get_admin_user)
):
    """
    Fetch system audit logs (Admin only).
    """
    logs = db_connection.execute_read(
        """
        SELECT l.log_id, l.action, l.ip_address, l.timestamp, l.status, l.details,
               u.name as user_name, u.email as user_email
        FROM audit_logs l
        LEFT JOIN users u ON l.user_id = u.user_id
        ORDER BY l.timestamp DESC
        LIMIT %s OFFSET %s
        """,
        (limit, offset)
    )
    return {"status": "success", "data": logs}

@router.get("/users")
def get_all_users(current_admin: dict = Depends(users.get_admin_user)):
    """
    Retrieve all registered user profiles (Admin only).
    """
    all_users = db_connection.execute_read(
        "SELECT user_id, name, email, phone, role FROM users ORDER BY user_id ASC"
    )
    return {"status": "success", "data": all_users}
