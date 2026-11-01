import os

# Tests use a throwaway in-memory database, never your real requests.db.
# conftest.py runs before any test file imports the app.
os.environ["REQUESTS_DB"] = ":memory:"
