"""pytest configuration — exclude manual debug scripts from CI collection."""

collect_ignore = [
    "test_http_chat.py",       # module-level HTTP calls to localhost:8000
    "test_login_response.py",  # module-level HTTP calls to localhost:8000
    "test_password.py",        # module-level DB query + exit(1)
    "test_db.py",              # module-level print/diagnostic code
    "test_chat_flow.py",       # requires seeded DB data to run
]
