import sqlite3
from functools import wraps

from src.utils.exceptions import DatabaseError, NotFoundError, ValidationError
from src.utils.logger import get_logger

logger = get_logger(__name__)


def handle_db_errors(fn):
    """Decorator that catches sqlite3 errors and re-raises as DatabaseError."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except sqlite3.OperationalError as e:
            logger.error("DB operational error in %s: %s", fn.__qualname__, e)
            raise DatabaseError(f"Database operation failed: {e}", original=e) from e
        except sqlite3.IntegrityError as e:
            logger.error("DB integrity error in %s: %s", fn.__qualname__, e)
            raise DatabaseError(f"Data integrity violation: {e}", original=e) from e
    return wrapper


def register_flask_error_handlers(app):
    """Attach JSON error handlers to a Flask app."""
    from flask import jsonify

    @app.errorhandler(NotFoundError)
    def handle_not_found(e):
        logger.warning("Not found: %s", e)
        return jsonify({"error": str(e)}), 404

    @app.errorhandler(ValidationError)
    def handle_validation(e):
        logger.warning("Validation error: %s", e)
        return jsonify({"error": str(e)}), 422

    @app.errorhandler(DatabaseError)
    def handle_database(e):
        logger.error("Database error: %s", e)
        return jsonify({"error": "A database error occurred."}), 500

    @app.errorhandler(Exception)
    def handle_generic(e):
        logger.exception("Unhandled exception: %s", e)
        return jsonify({"error": "An unexpected error occurred."}), 500
