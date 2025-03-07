import logging
from time import time

from django.conf import settings

logger = logging.getLogger(__name__)

class LogSlowRequestsMiddleware:
    """
    Middleware to enforce automatic logout after a period of inactivity.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout_minutes = getattr(settings, "LOG_SLOW_TREASHHOLDp\_SECONDS", 15)

    def __call__(self, request):
        start_time = time()

        response = self.get_response(request)

        duration = time() - start_time
        if duration > self.timeout_minutes:
            user = request.user if request.user.is_authenticated else "Anonymous"
            logger.info(f"User: {user}, Method: {request.method}, Path: {request.path}, Status: {response.status_code}, Time: {duration:.3f}s")

        return response
