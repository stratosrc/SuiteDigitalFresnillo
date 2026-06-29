"""WSGI entry point for Apache/Passenger or mod_wsgi-style hosts.

FastAPI is an ASGI application. Some Apache-based shared hosts only expose a
WSGI entry point named passenger_wsgi.py, so this adapter lets the same app run
there without rewriting the backend.
"""

from a2wsgi import ASGIMiddleware

from web_app.main import app


application = ASGIMiddleware(app)

