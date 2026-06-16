from fastapi import Request, HTTPException, status
import time
from collections import defaultdict
import logging

logger = logging.getLogger("rate_limiter")

# In-memory store for rate limiting: ip_endpoint -> list of request timestamps
_request_history = defaultdict(list)

# Limits configuration: (max_requests, window_seconds)
LIMITS = {
    "search": (10, 60),      # Search destinations: max 10 requests per minute
    "flights": (15, 60),     # Search flights: max 15 requests per minute
    "general": (60, 60)      # General API limits: max 60 requests per minute
}

def is_rate_limited(ip: str, category: str = "general") -> bool:
    """
    Returns True if the IP has exceeded the limit in the sliding window.
    """
    now = time.time()
    max_reqs, window = LIMITS.get(category, LIMITS["general"])
    
    key = f"{ip}:{category}"
    history = _request_history[key]
    
    # Filter out timestamps outside the sliding window
    _request_history[key] = [t for t in history if now - t < window]
    history = _request_history[key]
    
    if len(history) >= max_reqs:
        logger.warning(f"Rate limit exceeded for IP: {ip} in category: {category}")
        return True
        
    # Log this request timestamp
    _request_history[key].append(now)
    return False

def rate_limit_dependency(category: str = "general"):
    """
    FastAPI Dependency that checks rate limit.
    """
    def check_limit(request: Request):
        # Fallback to local loopback if client host is missing
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        if is_rate_limited(client_ip, category):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests for category '{category}'. Please try again in a minute."
            )
    return check_limit
