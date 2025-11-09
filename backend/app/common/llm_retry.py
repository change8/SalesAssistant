"""Enhanced LLM client wrapper with retry logic and structured logging."""

from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable, Dict, Optional, TypeVar

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
    after_log,
)

try:
    import requests
except ImportError:
    requests = None  # type: ignore

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

logger = logging.getLogger(__name__)

T = TypeVar("T")


# Define retryable exceptions
RETRYABLE_HTTP_EXCEPTIONS = []
if requests:
    RETRYABLE_HTTP_EXCEPTIONS.extend([
        requests.Timeout,
        requests.ConnectionError,
        requests.ReadTimeout,
    ])
if httpx:
    RETRYABLE_HTTP_EXCEPTIONS.extend([
        httpx.TimeoutException,
        httpx.ConnectError,
        httpx.ReadTimeout,
    ])


def is_retryable_http_error(exception: Exception) -> bool:
    """Check if HTTP error is retryable (5xx or connection issues)."""
    if any(isinstance(exception, exc_type) for exc_type in RETRYABLE_HTTP_EXCEPTIONS):
        return True

    # Check for 5xx HTTP status codes
    if requests and isinstance(exception, requests.HTTPError):
        if exception.response and 500 <= exception.response.status_code < 600:
            return True

    if httpx and isinstance(exception, httpx.HTTPStatusError):
        if 500 <= exception.response.status_code < 600:
            return True

    return False


def log_llm_request(
    provider: str,
    model: str,
    prompt_tokens: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Log LLM request with structured data.

    Args:
        provider: LLM provider name (e.g., "openai", "dashscope")
        model: Model name
        prompt_tokens: Estimated prompt token count
        metadata: Additional metadata to log
    """
    log_data = {
        "event": "llm_request",
        "provider": provider,
        "model": model,
        "prompt_tokens": prompt_tokens,
    }
    if metadata:
        log_data.update(metadata)

    logger.info(f"LLM request to {provider}/{model}", extra=log_data)


def log_llm_response(
    provider: str,
    model: str,
    duration_ms: float,
    success: bool,
    error: Optional[str] = None,
    response_tokens: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Log LLM response with structured data.

    Args:
        provider: LLM provider name
        model: Model name
        duration_ms: Request duration in milliseconds
        success: Whether request succeeded
        error: Error message if failed
        response_tokens: Response token count
        metadata: Additional metadata to log
    """
    log_data = {
        "event": "llm_response",
        "provider": provider,
        "model": model,
        "duration_ms": round(duration_ms, 2),
        "success": success,
        "response_tokens": response_tokens,
    }
    if error:
        log_data["error"] = error
    if metadata:
        log_data.update(metadata)

    if success:
        logger.info(f"LLM response from {provider}/{model} ({duration_ms:.0f}ms)", extra=log_data)
    else:
        logger.error(f"LLM request failed: {error}", extra=log_data)


def create_llm_retry_decorator(
    max_attempts: int = 3,
    min_wait_seconds: float = 2.0,
    max_wait_seconds: float = 30.0,
) -> Callable:
    """Create a retry decorator for LLM calls.

    Uses exponential backoff with jitter for retries.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait_seconds: Minimum wait time between retries
        max_wait_seconds: Maximum wait time between retries

    Returns:
        Retry decorator
    """
    return retry(
        retry=retry_if_exception_type(tuple(RETRYABLE_HTTP_EXCEPTIONS + [RuntimeError])),
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(
            multiplier=1,
            min=min_wait_seconds,
            max=max_wait_seconds,
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO),
        reraise=True,
    )


def with_llm_logging(
    provider: str,
    model: str,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to add structured logging to LLM calls.

    Args:
        provider: LLM provider name
        model: Model name

    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            start_time = time.time()
            error_msg = None

            # Log request
            log_llm_request(provider, model)

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                log_llm_response(provider, model, duration_ms, success=True)
                return result
            except Exception as exc:
                duration_ms = (time.time() - start_time) * 1000
                error_msg = str(exc)
                log_llm_response(provider, model, duration_ms, success=False, error=error_msg)
                raise

        return wrapper
    return decorator


def safe_timeout(timeout_value: Any, default: float = 60.0) -> Optional[float]:
    """Convert timeout configuration to a safe float value.

    Args:
        timeout_value: Timeout value from config (could be 0, None, string, etc.)
        default: Default timeout in seconds

    Returns:
        Float timeout value or None (for infinite wait)
    """
    try:
        numeric = float(timeout_value) if timeout_value is not None else default
    except (TypeError, ValueError):
        logger.warning(f"Invalid timeout value: {timeout_value}, using default {default}s")
        return default

    # 0 or negative means wait forever (None in requests/httpx)
    if numeric <= 0:
        logger.info("LLM timeout set to infinite (0 or negative value)")
        return None

    # Warn if timeout is very long
    if numeric > 300:  # 5 minutes
        logger.warning(f"Very long timeout configured: {numeric}s")

    return numeric
