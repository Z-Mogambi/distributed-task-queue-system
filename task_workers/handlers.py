import time
import random
import requests


JOB_HANDLERS = {}

def process_job(job):
    """
    method routes job into appropriate handler by getting job type from dict, look up the handler in
    JOB_HANDLERS and if the handle exists call it with the payload.
    raise exception if no handler and return result
    """
    job_type = job.get("type")
    if not job_type:
        raise ValueError("Job type is missing from job dictionary")
    
    handler = JOB_HANDLERS.get(job_type)

    if handler is None:
        raise ValueError(f"There's no job handler for job type: '{job_type}'")
    payload = job.get("payload", {})

    return handler(payload)

def handle_webhook(payload):
    """
    Handles sending a webhook to an external service.
    Expects 'url' and 'data' in the payload.
    """
    url = payload.get("url")
    if not url:
        raise ValueError("URL is missing from payload for webhook")

    data = payload.get("data", {})

    print(f"Sending webhook to: {url}...")

    try:
        # Make the actual HTTP POST request with a timeout
        response = requests.post(url, json=data, timeout=10)

        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        return {
            "status": "success",
            "response": {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text[:250] # Truncate body to avoid storing large responses
            },
            "timestamp": int(time.time())
        }
    except requests.exceptions.RequestException as e:
        # This will catch connection errors, timeouts, and bad status codes,
        # triggering the fail_job logic in the worker.
        raise Exception(f"Webhook call failed: {e}")


def handle_flaky_service(payload):
    """
    Handles jobs that call an external webhook that may fail.
    This simulates calling a service that is unreliable.
    """
    url = payload.get("url")
    if not url:
        raise ValueError("URL is missing from payload for flaky_service")

    print(f"Calling external service webhook: {url}...")
    
    try:
        # Make the actual HTTP request with a timeout
        response = requests.get(url, timeout=10)
        
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()
        
        return {
            "status": "success",
            "response": {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text[:250] # Truncate body to avoid storing large responses
            },
            "timestamp": int(time.time())
        }
    except requests.exceptions.RequestException as e:
        # This will catch connection errors, timeouts, and bad status codes,
        # triggering the fail_job logic in the worker.
        raise Exception(f"External service call failed: {e}")

JOB_HANDLERS["webhook"] = handle_webhook
JOB_HANDLERS["flaky_service"] = handle_flaky_service
