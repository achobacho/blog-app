from django.http import HttpResponseForbidden

class RestrictSwaggerDocsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == '/api/docs':
            user = request.user
            if not user.is_authenticated or not user.is_staff or not user.has_perm("core.view_api_docs"):
                return HttpResponseForbidden("You don't have permission to view the API docs.")
        return self.get_response(request)

