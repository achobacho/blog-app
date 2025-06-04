from django.http import HttpResponseForbidden

class RestrictSwaggerDocsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/api/docs' and (not request.user.is_authenticated or not request.user.is_staff):
            return HttpResponseForbidden("You must be an admin to view the API docs.")
        return self.get_response(request)
