"""
Rate limiting middleware for API protection.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.upload_requests = defaultdict(list)
    
    def _clean_old_requests(self, ip: str, window_seconds: int):
        """Remove requests older than the time window."""
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        self.requests[ip] = [
            timestamp for timestamp in self.requests[ip]
            if timestamp > cutoff
        ]
    
    def _clean_old_uploads(self, ip: str, window_seconds: int):
        """Remove upload requests older than the time window."""
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        self.upload_requests[ip] = [
            timestamp for timestamp in self.upload_requests[ip]
            if timestamp > cutoff
        ]
    
    def is_allowed(self, ip: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        """
        Check if request is allowed under rate limit.
        
        Args:
            ip: Client IP address
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds
            
        Returns:
            True if allowed, False otherwise
        """
        self._clean_old_requests(ip, window_seconds)
        
        if len(self.requests[ip]) >= max_requests:
            return False
        
        self.requests[ip].append(datetime.now())
        return True
    
    def is_upload_allowed(self, ip: str, max_uploads: int = 5, window_seconds: int = 600) -> bool:
        """
        Check if upload request is allowed under rate limit.
        
        Args:
            ip: Client IP address
            max_uploads: Maximum uploads allowed (default: 5)
            window_seconds: Time window in seconds (default: 600 = 10 minutes)
            
        Returns:
            True if allowed, False otherwise
        """
        self._clean_old_uploads(ip, window_seconds)
        
        if len(self.upload_requests[ip]) >= max_uploads:
            return False
        
        self.upload_requests[ip].append(datetime.now())
        return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to apply rate limiting to requests."""
    
    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Check general rate limit (60 req/min)
        if not self.rate_limiter.is_allowed(client_ip, max_requests=60, window_seconds=60):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later. (Limit: 60 requests/minute)"
            )
        
        # Check upload rate limit (5 uploads/10 min)
        if request.url.path == "/api/upload" and request.method == "POST":
            if not self.rate_limiter.is_upload_allowed(client_ip, max_uploads=5, window_seconds=600):
                logger.warning(f"Upload rate limit exceeded for IP: {client_ip}")
                raise HTTPException(
                    status_code=429,
                    detail="Too many uploads. Please try again later. (Limit: 5 uploads per 10 minutes)"
                )
        
        response = await call_next(request)
        return response
