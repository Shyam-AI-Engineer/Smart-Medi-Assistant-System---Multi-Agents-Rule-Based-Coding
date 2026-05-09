"""Redirect requests without trailing slashes to their trailing-slash equivalents."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse


class TrailingSlashMiddleware(BaseHTTPMiddleware):
    """
    Add trailing slashes to API requests that need them.

    This runs BEFORE routing, so it catches requests early and redirects
    them to the properly-slashed version.
    """
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Only redirect GET requests (not POST/PUT/DELETE which may not handle redirects well)
        # Only apply to API routes that typically need trailing slashes
        # (not files, not root, not already have trailing slash)
        if (
            request.method == "GET" and
            path.startswith('/api/') and
            not path.endswith('/') and
            path != '/' and
            '.' not in path.split('/')[-1]  # Avoid redirecting files
        ):
            # Redirect to version with trailing slash
            query_string = f"?{request.url.query}" if request.url.query else ""
            new_path = path + '/' + query_string
            return RedirectResponse(url=new_path, status_code=307)

        return await call_next(request)
