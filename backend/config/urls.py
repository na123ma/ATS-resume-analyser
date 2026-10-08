from django.urls import include, path
from django.http import JsonResponse

def home(request):
    return JsonResponse({
        "status": "success",
        "message": "Skillentra AI Backend Running Successfully",
        "framework": "Django",
        "hosting": "Render"
    })
urlpatterns = [
    path("", home, name="home"),
    path('api/', include('api.urls'))
]
