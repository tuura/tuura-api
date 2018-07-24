import json

from rq import Queue
from redis import Redis
from django.http import HttpResponse
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


job_queue = Queue(connection=Redis())


def jsonify(handler):
    """Create a Django view from a function with type json -> json."""

    def inner(self, request):
        request_json = json.loads(request.body) if request.body else {}
        results = handler(self, request_json)
        return JsonResponse(results)

    return inner


def get_error(msg):
    return {"result": "error", "description": msg}


@method_decorator(csrf_exempt, name='dispatch')
class Jobs(View):

    @jsonify
    def put(self, request):
        x = int(request.get("x", "0"))
        job = job_queue.enqueue("worker.analyze_network", x)
        return {"result": "queued for processing", "id": job.id}


    @jsonify
    def get(self, request):

        job_id = request.get("id")

        if not job_id:
            return get_error("job id missing")

        job = job_queue.fetch_job(job_id)

        if not job:
            return get_error("invalid job id")

        return {"result": "success", "job output": job.result}
