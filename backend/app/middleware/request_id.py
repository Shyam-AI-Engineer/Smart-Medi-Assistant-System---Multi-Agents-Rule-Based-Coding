"""Request-ID middleware.

Assigns a unique ID to every request so that all log lines for a single
HTTP call share a common trace token.

Behaviour:
- If the caller sends `X-Request-ID`, that value is reused (useful for
  frontend-to-backend tracing).
- Otherwise a new UUID4 is generated.
- The ID is always echoed back in the response header `X-Request-ID`.
- The ID is stored in a context variable (`request_id_ctx`) so that log
  handlers and service code can read it without threading the value
  through every function call.
"""
import uuid
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(_HEADER) or str(uuid.uuid4())
        token = request_id_ctx.set(request_id)
        try:
            response: Response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        response.headers[_HEADER] = request_id
        return response


def get_request_id() -> str:
    """Return the current request ID (safe to call from any async context)."""
    return request_id_ctx.get()
