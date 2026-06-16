from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel
from datetime import datetime
from backend.database import db_connection
from backend.api import users
from backend.services import audit_service

router = APIRouter(prefix="/api/bookings", tags=["Bookings"])

# Pydantic Schema
class BookingCreate(BaseModel):
    user_id: int
    flight_id: int

@router.post("", status_code=status.HTTP_201_CREATED)
def create_booking(
    booking: BookingCreate, 
    request: Request,
    current_user: dict = Depends(users.get_current_user)
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Governance check: Users can only create bookings for themselves, unless Admin
    if current_user["user_id"] != booking.user_id and current_user["role"] != "Admin":
        audit_service.log_action(current_user["user_id"], "create_booking_unauthorized", client_ip, "Failed", f"Tried booking for user_id {booking.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot book flights for other users."
        )
        
    # Verify flight exists
    flight = db_connection.execute_read(
        "SELECT * FROM flights WHERE flight_id = %s",
        (booking.flight_id,)
    )
    if not flight:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flight not found"
        )
        
    # Create booking
    booking_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    booking_id = db_connection.execute_query(
        "INSERT INTO bookings (user_id, flight_id, booking_date, status) VALUES (%s, %s, %s, %s)",
        (booking.user_id, booking.flight_id, booking_date, "Confirmed")
    )
    
    audit_service.log_action(booking.user_id, "flight_booked", client_ip, "Success", f"Booking ID: {booking_id} | Flight ID: {booking.flight_id}")
    
    return {
        "status": "success",
        "booking_id": booking_id,
        "message": "Booking confirmed successfully",
        "data": {
            "booking_id": booking_id,
            "user_id": booking.user_id,
            "flight": flight[0],
            "booking_date": booking_date,
            "status": "Confirmed"
        }
    }

@router.get("/user/{user_id}")
def get_user_bookings(
    user_id: int, 
    request: Request,
    current_user: dict = Depends(users.get_current_user)
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Governance check: Users can only view their own bookings, unless Admin
    if current_user["user_id"] != user_id and current_user["role"] != "Admin":
        audit_service.log_action(current_user["user_id"], "view_bookings_unauthorized", client_ip, "Failed", f"Tried viewing bookings for user_id {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot view other users' booking history."
        )
        
    query = """
        SELECT b.booking_id, b.booking_date, b.status, 
               f.flight_id, f.airline, f.source_city, f.destination_city, 
               f.departure_time, f.arrival_time, f.price
        FROM bookings b
        JOIN flights f ON b.flight_id = f.flight_id
        WHERE b.user_id = %s
        ORDER BY b.booking_date DESC
    """
    bookings = db_connection.execute_read(query, (user_id,))
    audit_service.log_action(current_user["user_id"], "bookings_viewed", client_ip, "Success", f"Fetched {len(bookings)} bookings")
    return {"status": "success", "data": bookings}

@router.delete("/{booking_id}")
def cancel_booking(
    booking_id: int, 
    request: Request,
    current_user: dict = Depends(users.get_current_user)
):
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Verify booking exists
    booking = db_connection.execute_read(
        "SELECT * FROM bookings WHERE booking_id = %s",
        (booking_id,)
    )
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
        
    booking_data = booking[0]
    
    # Governance check: Users can only cancel their own bookings, unless Admin
    if current_user["user_id"] != booking_data["user_id"] and current_user["role"] != "Admin":
        audit_service.log_action(current_user["user_id"], "cancel_booking_unauthorized", client_ip, "Failed", f"Tried cancelling booking_id {booking_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cannot cancel bookings for other users."
        )
        
    db_connection.execute_query(
        "DELETE FROM bookings WHERE booking_id = %s",
        (booking_id,)
    )
    
    audit_service.log_action(booking_data["user_id"], "flight_cancelled", client_ip, "Success", f"Booking ID: {booking_id}")
    
    return {"status": "success", "message": "Booking cancelled successfully"}
