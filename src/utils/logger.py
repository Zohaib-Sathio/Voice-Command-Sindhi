"""
Request-scoped logging utility for CloudWatch log filtering.
Each request gets a unique UUID that is prepended to all log messages.
"""
import sys
from contextvars import ContextVar
from uuid import uuid4

# Context variable to store request ID per async context
_request_id: ContextVar[str] = ContextVar('request_id', default='')


def set_request_id(request_id: str = None) -> str:
    """
    Set the request ID for the current async context.
    If no ID is provided, generates a new UUID.
    
    Args:
        request_id: Optional request ID. If None, generates a new UUID.
    
    Returns:
        The request ID that was set.
    """
    if request_id is None:
        request_id = str(uuid4())
    _request_id.set(request_id)
    return request_id


def get_request_id() -> str:
    """
    Get the current request ID from context.
    
    Returns:
        The request ID, or empty string if not set.
    """
    try:
        return _request_id.get()
    except LookupError:
        return ''


def log(*args, **kwargs):
    """
    Logging function that prepends request ID to all log messages.
    This is a drop-in replacement for print() that adds UUID prefix.
    
    Usage:
        log("Hello", "world")  # Output: [<uuid>] Hello world
        log(f"Value: {value}")  # Output: [<uuid>] Value: 123
    """
    request_id = get_request_id()
    prefix = f"[{request_id}] " if request_id else ""
    
    # Handle both positional and keyword arguments like print()
    # Convert all args to strings and join them
    message = ' '.join(str(arg) for arg in args)
    
    # Handle sep and end kwargs like print()
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    flush = kwargs.get('flush', False)
    
    # Reconstruct message with custom sep if multiple args
    if len(args) > 1:
        message = sep.join(str(arg) for arg in args)
    elif len(args) == 1:
        message = str(args[0])
    else:
        message = ''
    
    # Print with prefix
    print(f"{prefix}{message}", end=end, flush=flush)
    if flush:
        sys.stdout.flush()

