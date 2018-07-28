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
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


job_queue = Queue(connection=Redis())
job_ids = {}  # map (job id) -> (rq id)


def make_error(status_code, msg):
    """Return JsonResponse object describing an error."""
    response = JsonResponse({"error": msg})
    response.status_code = status_code
    return response


@method_decorator(csrf_exempt, name='dispatch')
class Jobs(View):

    def put(self, request):

        rjson = json.loads(request.body) if request.body else {}
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
            if not fd in rjson:
                return make_error(400, "missing %s field" % fd)

        # Check that field values can be cast to field types

        perturb_args = {}

        for fd, fd_type in required_fields:
            try:
                perturb_args[fd] = fd_type(rjson[fd])
            except ValueError:
                return make_error(400, "field %s must be of type %s" % (fd, fd_type.__name__))

        try:
            job = job_queue.enqueue("worker.perturb", **perturb_args, timeout=timeout)
        except:
            return make_error(500, "backend queue unavailable")

        job_id = create_job_id()
        job_ids[job_id] = job.id
        response = {"status": "queued for processing", "id": job_id}
        return JsonResponse(response)

    def get(self, request, job_id):

        if not job_id:
            return make_error(400, "missing job id")

        if job_id not in job_ids:
            return make_error(404, "invalid job id")

        try:
            job = job_queue.fetch_job(job_ids[job_id])
        except:
            return make_error(500, "backend queue unavailable")

        if not job:
            return make_error(400, "job not found")

        if job.is_finished:
            return JsonResponse({"status": "completed", "result": job.result})
        elif job.is_queued:
            return JsonResponse({"status": "queued for processing"})
        elif job.is_started:
            return JsonResponse({"status": "in progress"})
        elif job.is_failed:
            return JsonResponse({"status": "job failed"})

        return make_error(500, "job information unavailable")
