import json

from rq import Queue
from redis import Redis
from random import randint
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseNotFound
from django.http import HttpResponseServerError
from django.http import JsonResponse
from django.views import View
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


job_queue = Queue(connection=Redis())
job_ids = {}  # map (job id) -> (rq id)


def jsonify(handler):
    """Create a Django view from a function with type json -> json."""

    def inner(self, request):
        request_json = json.loads(request.body) if request.body else {}
        return handler(self, request_json)

    return inner


@method_decorator(csrf_exempt, name='dispatch')
class Jobs(View):

    @jsonify
    def put(self, request):

        timeout = 180  # job timeout (seconds)

        job_id_digits = 3

        required_fields = [
            ("graphml", str),
            ("remove_max", float),
            ("nrepeats", int),
            ("granularity", int),
            ("method", str),
        ]

        def create_job_id():
            mn = 10 ** (job_id_digits - 1)
            mx = 10 ** (job_id_digits) - 1
            return str(randint(mn, mx))

        # Check that fields are present

        for fd, _ in required_fields:
            if not fd in request:
                return HttpResponseBadRequest("missing %s field" % fd)

        # Check that field values can be cast to field types

        perturb_args = {}

        for fd, fd_type in required_fields:
            try:
                perturb_args[fd] = fd_type(request[fd])
            except ValueError:
                body = "field %s must be of type %s" % (fd, fd_type.__name__)
                return HttpResponseBadRequest(body)

        job = job_queue.enqueue("worker.perturb", **perturb_args, timeout=timeout)
        job_id = create_job_id()
        job_ids[job_id] = job.id
        response = {"status": "queued for processing", "id": job_id}
        return JsonResponse(response)


    # @jsonify
    def get(self, request, job_id):

        if not job_id:
            return HttpResponseBadRequest("missing job id")

        if job_id not in job_ids:
            return HttpResponseBadRequest("invalid job id")

        try:
            job = job_queue.fetch_job(job_ids[job_id])
        except:
            return HttpResponseServerError("backend queue unavailable")

        if not job:
            return HttpResponseNotFound("job not found")

        if job.is_finished:
            response = {"status": "completed", "result": job.result}
        elif job.is_queued:
            response = {"status": "queued for processing"}
        elif job.is_started:
            response = {"status": "in progress"}
        elif job.is_failed:
            response = {"status": "job failed"}

        return JsonResponse(response)
