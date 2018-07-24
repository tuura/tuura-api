import json

from rq import Queue
from redis import Redis
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
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
        return handler(self, request_json)

    return inner


def get_error(msg):
    return {"result": "error", "description": msg}


@method_decorator(csrf_exempt, name='dispatch')
class Jobs(View):

    @jsonify
    def put(self, request):
        x = int(request.get("x", "0"))
        job = job_queue.enqueue("worker.analyze_network", x)
        response = {"status": "queued for processing", "id": job.id}
        return JsonResponse(response)


    @jsonify
    def get(self, request):

        job_id = request.get("id")

        if not job_id:
            return HttpResponseBadRequest()

        job = job_queue.fetch_job(job_id)

        if not job:
            return HttpResponseNotFound()

        if job.is_finished:
            response = {"status": "completed", "result": job.result}
        elif job.is_queued:
            response = {"status": "queued for processing"}
        elif job.is_started:
            response = {"status": "in progress"}

        return JsonResponse(response)
