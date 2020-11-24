from logging import getLogger

from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

_log = getLogger(__name__)

class HealthCheckMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/health':
            return HttpResponse('ok')
        return self.get_response(request)

class LogExceptionMiddleWare(MiddlewareMixin):
    def process_exception(self, request, exception):
        _log.exception('Exception encountered', exc_info=True)