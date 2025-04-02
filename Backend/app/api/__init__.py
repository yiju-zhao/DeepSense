from app.api.routes import api_router
from app.api.errors import add_error_handlers
from app.api.middleware import add_logging_middleware

# Import all API components here to make them available when importing from app.api