import json

from rq import Queue
from redis import Redis
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


job_queue = Queue(connection=Redis())


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


def get_error(msg):
    return {"result": "error", "description": msg}


@api
def jobs(request):
    x = int(request.get("x", "0"))
    job = job_queue.enqueue("worker.analyze_network", x)
    return {"result": "queued for processing", "id": job.id}


@api
def results(request):

    job_id = request.get("id")

    if not job_id:
        return get_error("job id missing")

    job = job_queue.fetch_job(job_id)

    if not job:
        return get_error("invalid job id")

    return {"result": "success", "job output": job.result}
