import os
from uuid import uuid4
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
def health_check(request):
    return JsonResponse({"status": "ok"})


@csrf_exempt
def tinymce_image_upload(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        ext = os.path.splitext(file.name)[-1]
        filename = f"{uuid4().hex}{ext}"
        filepath = os.path.join(settings.MEDIA_ROOT, 'uploads', filename)

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, 'wb+') as dest:
            for chunk in file.chunks():
                dest.write(chunk)

        file_url = f"{settings.MEDIA_URL}uploads/{filename}"
        return JsonResponse({'location': file_url})

    return JsonResponse({'error': 'Invalid request'}, status=400)