import time
import random

def handle_email(payload):
    """
    simulating an email being sent (time.sleep(2) to simulate a network call) and returning
    a success result with message_id
    1. Print "Sending email to {to}..."
    2. Sleep for 2 seconds (simulate network call)
    3. Return success result with message_id
    """
    print(f"sending email to {payload['to']}...")

    time.sleep(2)

    message_id = f"msg_{random.randint(100000, 999999)}"
    return {                                                                                                                                                
        "status": "sent",                                                                                                                                   
        "message_id": message_id,                                                                                                                           
        "to": payload['to']                                                                                                                                 
    }


def handle_image_processing(payload):
    """
    simulating an image processing by printing and time.sleep(3) then returning
    result with output url
    """

    print(f"Processing image {payload['image_url']}...")

    time.sleep(3)

    return {
        "status": "processed",
        "output_url": "https://cdn.example.com/processed_abc123.jpg",
        "operations_applied": payload['operations']
    }
    

def handle_calculation(payload):
    """
    given a list of numbers, calculate sum, average, min, max of numbers and return results
    {
        "numbers": [1, 2, 3, 4, 5]
    }
    """
    numbers= payload.get("numbers", [])

    if not numbers:
        return {
            "sum": 0,
            "average": 0,
            "min": None,
            "max": None
        }

    return {
        "sum": sum(numbers),
        "average": sum(numbers) / len(numbers),
        "min": min(numbers),
        "max": max(numbers)
    }

JOB_HANDLERS = {
    "email": handle_email,
    "image_processing": handle_image_processing,
    "calculation": handle_calculation
}

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