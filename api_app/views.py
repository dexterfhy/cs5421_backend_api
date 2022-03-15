from django.http import HttpResponse

def healthcheck(request):
    return HttpResponse(content='Hello, world', status=201)
