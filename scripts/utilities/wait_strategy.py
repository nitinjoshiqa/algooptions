#!/usr/bin/env python3
"""
Advanced retry and rate-limiting strategy for API calls
Handles timeouts, retries with exponential backoff, and adaptive delays
"""

import time
import random
from functools import wraps
from typing import Callable, Any, Optional

class APIRateLimiter:
    """Manages API rate limiting and retry strategy"""
    
    def __init__(self, 
                 base_delay: float = 0.5,
                 max_delay: float = 10.0,
                 max_retries: int = 3,
                 backoff_factor: float = 2.0):
        """
        Initialize rate limiter
        
        Args:
            base_delay: Initial delay between requests (seconds)
            max_delay: Maximum delay cap (seconds)
            max_retries: Max retry attempts on failure
            backoff_factor: Exponential backoff multiplier
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.last_request_time = 0
        self.failure_count = 0
        self.success_count = 0
    
    def get_current_delay(self) -> float:
        """Calculate current delay based on failure count"""
        delay = self.base_delay * (self.backoff_factor ** self.failure_count)
        return min(delay, self.max_delay)
    
    def wait(self) -> None:
        """Wait before next request with adaptive delay"""
        delay = self.get_current_delay()
        if delay > 0:
            # Add small random jitter to avoid thundering herd
            jitter = random.uniform(0, delay * 0.1)
            time.sleep(delay + jitter)
        self.last_request_time = time.time()
    
    def record_success(self) -> None:
        """Record successful API call"""
        self.success_count += 1
        # Gradually reset failure count on success
        if self.failure_count > 0:
            self.failure_count = max(0, self.failure_count - 0.5)
    
    def record_failure(self) -> None:
        """Record failed API call"""
        self.failure_count += 1
    
    def reset(self) -> None:
        """Reset counters"""
        self.failure_count = 0
        self.success_count = 0
    
    def stats(self) -> dict:
        """Get current stats"""
        return {
            'success': self.success_count,
            'failures': self.failure_count,
            'current_delay': self.get_current_delay(),
        }


def retry_with_backoff(max_retries: int = 3, 
                       base_delay: float = 0.5,
                       backoff_factor: float = 2.0,
                       exceptions: tuple = (Exception,)):
    """
    Decorator: Retry function with exponential backoff
    
    Usage:
        @retry_with_backoff(max_retries=3, base_delay=1.0)
        def fetch_data(symbol):
            return yf.Ticker(symbol).info
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        # Exponential backoff
                        delay = base_delay * (backoff_factor ** (attempt - 1))
                        jitter = random.uniform(0, delay * 0.2)
                        wait_time = min(delay + jitter, 30)  # Cap at 30 seconds
                        print(f"[RETRY] Attempt {attempt + 1}/{max_retries + 1}, waiting {wait_time:.1f}s...")
                        time.sleep(wait_time)
                    
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        raise
                    continue
            
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def adaptive_rate_limit(limiter: APIRateLimiter, 
                       exceptions: tuple = (Exception,)):
    """
    Decorator: Apply adaptive rate limiting with automatic backoff
    
    Usage:
        limiter = APIRateLimiter(base_delay=0.3)
        
        @adaptive_rate_limit(limiter)
        def fetch_stock_data(symbol):
            return yf.Ticker(symbol).info
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Wait before request
            limiter.wait()
            
            try:
                result = func(*args, **kwargs)
                limiter.record_success()
                return result
            
            except exceptions as e:
                limiter.record_failure()
                raise
        
        return wrapper
    return decorator


class BatchRequestHandler:
    """Handles batches of API requests with smart rate limiting"""
    
    def __init__(self, 
                 batch_size: int = 10,
                 inter_batch_delay: float = 2.0,
                 request_delay: float = 0.3):
        """
        Initialize batch handler
        
        Args:
            batch_size: Number of requests per batch
            inter_batch_delay: Delay between batches (seconds)
            request_delay: Delay between individual requests
        """
        self.batch_size = batch_size
        self.inter_batch_delay = inter_batch_delay
        self.request_delay = request_delay
        self.processed = 0
        self.failed = 0
    
    def execute_batch(self, items: list, func: Callable) -> list:
        """
        Execute function on batch of items with rate limiting
        
        Args:
            items: List of items to process
            func: Function to apply to each item
        
        Returns:
            List of (item, result) tuples
        """
        results = []
        
        for batch_idx, i in enumerate(range(0, len(items), self.batch_size)):
            batch = items[i:i+self.batch_size]
            
            # Inter-batch delay
            if batch_idx > 0:
                jitter = random.uniform(0, self.inter_batch_delay * 0.2)
                time.sleep(self.inter_batch_delay + jitter)
            
            for item in batch:
                try:
                    # Delay between requests
                    time.sleep(self.request_delay)
                    result = func(item)
                    results.append((item, result))
                    self.processed += 1
                
                except Exception as e:
                    results.append((item, None))
                    self.failed += 1
                    print(f"[WARN] Failed to process {item}: {str(e)[:50]}")
        
        return results
    
    def stats(self) -> dict:
        """Get processing statistics"""
        return {
            'processed': self.processed,
            'failed': self.failed,
            'success_rate': self.processed / (self.processed + self.failed) if (self.processed + self.failed) > 0 else 0
        }


# Example usage helper
def create_smart_fetcher(use_aggressive: bool = False):
    """
    Factory: Create a smart API fetcher with optimal settings
    
    Args:
        use_aggressive: Use faster delays for high-speed networks
    
    Returns:
        Configured APIRateLimiter
    """
    if use_aggressive:
        return APIRateLimiter(
            base_delay=0.2,
            max_delay=5.0,
            max_retries=2,
            backoff_factor=1.5
        )
    else:
        return APIRateLimiter(
            base_delay=0.5,
            max_delay=15.0,
            max_retries=3,
            backoff_factor=2.0
        )
