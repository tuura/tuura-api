from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


def restful(handler):
    """Create a Django view from a function with type json -> json."""

    def restful_handler(*args, **kwargs):
        request = kwargs['request'] if 'request' in kwargs else args[0]

        if request.method == 'POST':
            data = json.loads(request.body) if request.body else {}
            results = handler(data)
            return JsonResponse(results)
        else:
            return JsonResponse({"error": "no POST data"})

    return restful_handler


def api(func):
    """Apply several decorators to create API-ready view function."""

    decorators = [restful, csrf_exempt]

    for dec in decorators:
        func = dec(func)

    return func


@api
def hello(request):
    return {"result": "Hello networks!"}
