import logging
from datetime import timedelta

from django.conf import settings
from django.shortcuts import redirect
from django.utils import timezone

logger = logging.getLogger(__name__)

class IdleTimeoutMiddleware:
    """
    Middleware to enforce automatic logout after a period of inactivity.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.timeout_minutes = getattr(settings, "IDLE_TIMEOUT", 15)

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)

        try:
            last_touch = request.session.get("last_touch")
            now = timezone.now()

            if last_touch:
                last_touch_time = timezone.datetime.fromisoformat(last_touch)
                if last_touch_time < now - timedelta(minutes=self.timeout_minutes):
                    logger.info(f"User {request.user} session expired due to inactivity.")
                    request.session.flush()  # Clear session
                    return redirect("/logout/")

            request.session["last_touch"] = now.isoformat()
        except Exception as e:
            logger.error(f"Error in IdleTimeoutMiddleware: {e}")

        return self.get_response(request)
